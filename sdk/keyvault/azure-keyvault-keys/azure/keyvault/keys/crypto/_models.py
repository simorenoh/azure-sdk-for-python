# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
from __future__ import annotations
from typing import Any, cast, Optional, NoReturn, Union, TYPE_CHECKING

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.padding import AsymmetricPadding, OAEP, PKCS1v15, PSS, MGF1
from cryptography.hazmat.primitives.asymmetric.rsa import (
    rsa_crt_dmp1,
    rsa_crt_dmq1,
    rsa_crt_iqmp,
    rsa_recover_prime_factors,
    RSAPrivateKey,
    RSAPrivateNumbers,
    RSAPublicKey,
    RSAPublicNumbers,
)
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
from cryptography.hazmat.primitives.hashes import Hash, HashAlgorithm, SHA1, SHA256, SHA384, SHA512
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    KeySerializationEncryption,
    PrivateFormat,
    PublicFormat,
)

from ._enums import EncryptionAlgorithm, KeyWrapAlgorithm, SignatureAlgorithm
from .._models import JsonWebKey

if TYPE_CHECKING:
    # Import client only during TYPE_CHECKING to avoid circular dependency
    from ._client import CryptographyClient


SIGN_ALGORITHM_MAP = {
    SHA256: SignatureAlgorithm.rs256,
    SHA384: SignatureAlgorithm.rs384,
    SHA512: SignatureAlgorithm.rs512,
}
OAEP_MAP = {SHA1: EncryptionAlgorithm.rsa_oaep, SHA256: EncryptionAlgorithm.rsa_oaep_256}
PSS_MAP = {
    SignatureAlgorithm.rs256: SignatureAlgorithm.ps256,
    SignatureAlgorithm.rs384: SignatureAlgorithm.ps384,
    SignatureAlgorithm.rs512: SignatureAlgorithm.ps512,
}


def get_encryption_algorithm(padding: AsymmetricPadding) -> EncryptionAlgorithm:
    """Maps an `AsymmetricPadding` to an encryption algorithm.

    :param padding: The padding to use.
    :type padding: ~cryptography.hazmat.primitives.asymmetric.padding.AsymmetricPadding

    :returns: The corresponding Key Vault encryption algorithm.
    :rtype: EncryptionAlgorithm
    """
    if isinstance(padding, OAEP):
        # Public algorithm property was only added in https://github.com/pyca/cryptography/pull/9582
        # _algorithm property has been available in every version of the OAEP class, so we use it as a backup
        try:
            algorithm = padding.algorithm  # type: ignore[attr-defined]
        except AttributeError:
            algorithm = padding._algorithm  # pylint:disable=protected-access
        mapped_algorithm = OAEP_MAP.get(type(algorithm))
        if mapped_algorithm is None:
            raise ValueError(f"Unsupported algorithm: {algorithm.name}")

        # Public mgf property was added at the same time as algorithm
        try:
            mgf = padding.mgf  # type: ignore[attr-defined]
        except AttributeError:
            mgf = padding._mgf  # pylint:disable=protected-access
        if not isinstance(mgf, MGF1):
            raise ValueError(f"Unsupported MGF: {mgf}")

    elif isinstance(padding, PKCS1v15):
        mapped_algorithm = EncryptionAlgorithm.rsa1_5
    else:
        raise ValueError(f"Unsupported padding: {padding.name}")

    return mapped_algorithm


def get_signature_algorithm(padding: AsymmetricPadding, algorithm: HashAlgorithm) -> SignatureAlgorithm:
    """Maps an `AsymmetricPadding` and `HashAlgorithm` to a signature algorithm.

    :param padding: The padding to use.
    :type padding: ~cryptography.hazmat.primitives.asymmetric.padding.AsymmetricPadding
    :param algorithm: The algorithm to use.
    :type algorithm: ~cryptography.hazmat.primitives.hashes.HashAlgorithm

    :returns: The corresponding Key Vault signature algorithm.
    :rtype: SignatureAlgorithm
    """
    mapped_algorithm = SIGN_ALGORITHM_MAP.get(type(algorithm))
    if mapped_algorithm is None:
        raise ValueError(f"Unsupported algorithm: {algorithm.name}")

    # If PSS padding is requested, use the PSS equivalent algorithm
    if isinstance(padding, PSS):
        mapped_algorithm = PSS_MAP.get(mapped_algorithm)

        # Public mgf property was only added in https://github.com/pyca/cryptography/pull/9582
        # _mgf property has been available in every version of the PSS class, so we use it as a backup
        try:
            mgf = padding.mgf  # type: ignore[attr-defined]
        except AttributeError:
            mgf = padding._mgf  # pylint:disable=protected-access
        if not isinstance(mgf, MGF1):
            raise ValueError(f"Unsupported MGF: {mgf}")

    # The only other padding accepted is PKCS1v15
    elif not isinstance(padding, PKCS1v15):
        raise ValueError(f"Unsupported padding: {padding.name}")

    return cast(SignatureAlgorithm, mapped_algorithm)


class KeyVaultRSAPublicKey(RSAPublicKey):
    """An `RSAPublicKey` implementation based on a key managed by Key Vault.

    This class should not be instantiated directly. Instead, use the
    :func:`~azure.keyvault.keys.crypto.CryptographyClient.create_rsa_public_key` method to create a key based on the
    client's key. Only synchronous clients and operations are supported at this time.
    """

    def __init__(self, client: "CryptographyClient", key_material: Optional[JsonWebKey] = None) -> None:
        self._client: "CryptographyClient" = client
        self._key: Optional[JsonWebKey] = key_material

    def encrypt(self, plaintext: bytes, padding: AsymmetricPadding) -> bytes:
        """Encrypts the given plaintext.

        :param bytes plaintext: Plaintext to encrypt.
        :param padding: The padding to use. Supported paddings are `OAEP` and `PKCS1v15`. For `OAEP` padding, supported
            hash algorithms are `SHA1` and `SHA256`. The only supported mask generation function is `MGF1`. See
            https://learn.microsoft.com/azure/key-vault/keys/about-keys-details for details.
        :type padding: ~cryptography.hazmat.primitives.asymmetric.padding.AsymmetricPadding

        :returns: The encrypted ciphertext, as bytes.
        :rtype: bytes
        """
        mapped_algorithm = get_encryption_algorithm(padding)
        result = self._client.encrypt(mapped_algorithm, plaintext)
        return result.ciphertext

    @property
    def key_size(self) -> int:
        """The bit length of the public modulus.

        :returns: The key's size.
        :rtype: int

        :raises ValueError: if the client is unable to obtain the key material from Key Vault.
        """
        if self._key is None:
            raise ValueError(
                "Key material could not be obtained from Key Vault. Only remote cryptographic operations "
                "(encrypt, verify) can be performed."
            )

        public_key = self.public_numbers().public_key()
        return public_key.key_size

    def public_numbers(self) -> RSAPublicNumbers:
        """Returns an `RSAPublicNumbers` representing the key's public numbers.

        :returns: The public numbers of the key.
        :rtype: RSAPublicNumbers

        :raises ValueError: if the client is unable to obtain the key material from Key Vault.
        """
        if self._key is None:
            raise ValueError(
                "Key material could not be obtained from Key Vault. Only remote cryptographic operations "
                "(encrypt, verify) can be performed."
            )

        e = int.from_bytes(self._key.e, "big")  # type: ignore[attr-defined]
        n = int.from_bytes(self._key.n, "big")  # type: ignore[attr-defined]
        return RSAPublicNumbers(e, n)

    def public_bytes(self, encoding: Encoding, format: PublicFormat) -> bytes:
        """Allows serialization of the key to bytes.

        This function uses the `cryptography` library's implementation.
        Encoding (`PEM` or `DER`) and format (`SubjectPublicKeyInfo` or `PKCS1`) are chosen to define the exact
        serialization.

        :param encoding: A value from the `Encoding` enum.
        :type encoding: ~cryptography.hazmat.primitives.serialization.Encoding
        :param format: A value from the `PublicFormat` enum.
        :type format: ~cryptography.hazmat.primitives.serialization.PublicFormat

        :returns: The serialized key.
        :rtype: bytes

        :raises ValueError: if the client is unable to obtain the key material from Key Vault.
        """
        if self._key is None:
            raise ValueError(
                "Key material could not be obtained from Key Vault. Only remote cryptographic operations "
                "(encrypt, verify) can be performed."
            )

        public_key = self.public_numbers().public_key()
        return public_key.public_bytes(encoding=encoding, format=format)

    def verify(
        self,
        signature: bytes,
        data: bytes,
        padding: AsymmetricPadding,
        algorithm: Union[Prehashed, HashAlgorithm],
    ) -> None:
        """Verifies the signature of the data.

        :param bytes signature: The signature to sign, as bytes.
        :param bytes data: The message string that was signed., as bytes.
        :param padding: The padding to use. Supported paddings are `PKCS1v15` and `PSS`. For `PSS`, the only supported
            mask generation function is `MGF1`. See https://learn.microsoft.com/azure/key-vault/keys/about-keys-details
            for details.
        :type padding: ~cryptography.hazmat.primitives.asymmetric.padding.AsymmetricPadding
        :param algorithm: The algorithm to sign with. Only `HashAlgorithm`s are supported -- specifically, `SHA256`,
            `SHA384`, and `SHA512`.
        :type algorithm: ~cryptography.hazmat.primitives.asymmetric.utils.Prehashed or
            cryptography.hazmat.primitives.hashes.HashAlgorithm

        :raises InvalidSignature: If the signature does not validate.
        """
        if isinstance(algorithm, Prehashed):
            raise ValueError("`Prehashed` algorithms are unsupported. Please provide a `HashAlgorithm` instead.")
        mapped_algorithm = get_signature_algorithm(padding, algorithm)
        digest = Hash(algorithm)
        digest.update(data)
        result = self._client.verify(mapped_algorithm, digest.finalize(), signature)
        if not result.is_valid:
            raise InvalidSignature(f"The provided signature '{signature!r}' is invalid.")

    def recover_data_from_signature(
        self, signature: bytes, padding: AsymmetricPadding, algorithm: Optional[HashAlgorithm]
    ) -> bytes:
        # pylint: disable=line-too-long
        """Recovers the signed data from the signature. Only supported with `cryptography` version 3.3 and above.

        This function uses the `cryptography` library's implementation.
        The data typically contains the digest of the original message string. The `padding` and `algorithm` parameters
        must match the ones used when the signature was created for the recovery to succeed.
        The `algorithm` parameter can also be set to None to recover all the data present in the signature, without
        regard to its format or the hash algorithm used for its creation.

        For `PKCS1v15` padding, this method returns the data after removing the padding layer. For standard signatures
        the data contains the full `DigestInfo` structure. For non-standard signatures, any data can be returned,
        including zero-length data.

        Normally you should use the `verify()` function to validate the signature. But for some non-standard signature
        formats you may need to explicitly recover and validate the signed data. The following are some examples:

        * Some old Thawte and Verisign timestamp certificates without `DigestInfo`.
        * Signed MD5/SHA1 hashes in TLS 1.1 or earlier (`RFC 4346 <https://datatracker.ietf.org/doc/html/rfc4346.html>`_, section 4.7).
        * IKE version 1 signatures without `DigestInfo` (`RFC 2409 <https://datatracker.ietf.org/doc/html/rfc2409.html>`_, section 5.1).

        :param bytes signature: The signature.
        :param padding: An instance of `AsymmetricPadding`. Recovery is only supported with some of the padding types.
        :type padding: ~cryptography.hazmat.primitives.asymmetric.padding.AsymmetricPadding
        :param algorithm: An instance of `HashAlgorithm`. Can be None to return all the data present in the signature.
        :type algorithm: ~cryptography.hazmat.primitives.hashes.HashAlgorithm

        :returns: The signed data.
        :rtype: bytes
        :raises NotImplementedError: if the local version of `cryptography` doesn't support this method.
        :raises ~cryptography.exceptions.InvalidSignature: if the signature is invalid.
        :raises ~cryptography.exceptions.UnsupportedAlgorithm: if the signature data recovery is not supported with
            the provided `padding` type.
        :raises ValueError: if the client is unable to obtain the key material from Key Vault.
        """
        if self._key is None:
            raise ValueError(
                "Key material could not be obtained from Key Vault. Only remote cryptographic operations "
                "(encrypt, verify) can be performed."
            )

        public_key = self.public_numbers().public_key()
        try:
            return public_key.recover_data_from_signature(signature=signature, padding=padding, algorithm=algorithm)
        except AttributeError as exc:
            raise NotImplementedError(
                "This method is only available on `cryptography`>=3.3. Update your package version to use this method."
            ) from exc

    def __eq__(self, other: object) -> bool:
        """Checks equality.

        :param object other: Another object to compare with this instance. Currently, only comparisons with
            `KeyVaultRSAPrivateKey` or `JsonWebKey` instances are supported.

        :returns: True if the objects are equal; False if the objects are unequal or if key material can't be obtained
            from Key Vault for comparison.
        :rtype: bool
        """
        if self._key is None:
            return False

        if isinstance(other, KeyVaultRSAPublicKey):
            return all(getattr(self._key, field) == getattr(other._key, field) for field in self._key._FIELDS)
        if isinstance(other, JsonWebKey):
            return all(getattr(self._key, field) == getattr(other, field) for field in self._key._FIELDS)
        return False

    def __copy__(self) -> KeyVaultRSAPublicKey:
        """Returns this instance since it is treated as immutable.

        :returns: This instance.
        :rtype: ~azure.keyvault.keys.crypto.KeyVaultRSAPublicKey
        """
        return self

    def verifier(  # pylint:disable=docstring-missing-param,docstring-missing-return,docstring-missing-rtype
        self, signature: bytes, padding: AsymmetricPadding, algorithm: HashAlgorithm
    ) -> NoReturn:
        """Not implemented. This method was deprecated in `cryptography` 2.0 and removed in 37.0.0."""
        raise NotImplementedError()


class KeyVaultRSAPrivateKey(RSAPrivateKey):
    """An `RSAPrivateKey` implementation based on a key managed by Key Vault.

    This class should not be instantiated directly. Instead, use the
    :func:`~azure.keyvault.keys.crypto.CryptographyClient.create_rsa_private_key` method to create a key based on the
    client's key. Only synchronous clients and operations are supported at this time.
    """

    def __init__(self, client: "CryptographyClient", key_material: Optional[JsonWebKey]) -> None:
        self._client: "CryptographyClient" = client
        self._key: Optional[JsonWebKey] = key_material

    def decrypt(self, ciphertext: bytes, padding: AsymmetricPadding) -> bytes:
        """Decrypts the provided ciphertext.

        :param bytes ciphertext: Encrypted bytes to decrypt.
        :param padding: The padding to use. Supported paddings are `OAEP` and `PKCS1v15`. For `OAEP` padding, supported
            hash algorithms are `SHA1` and `SHA256`. The only supported mask generation function is `MGF1`. See
            https://learn.microsoft.com/azure/key-vault/keys/about-keys-details for details.
        :type padding: ~cryptography.hazmat.primitives.asymmetric.padding.AsymmetricPadding

        :returns: The decrypted plaintext, as bytes.
        :rtype: bytes
        """
        mapped_algorithm = get_encryption_algorithm(padding)
        result = self._client.decrypt(mapped_algorithm, ciphertext)
        return result.plaintext

    @property
    def key_size(self) -> int:
        """The bit length of the public modulus.

        :returns: The key's size.
        :rtype: int

        :raises ValueError: if the client is unable to obtain the key material from Key Vault.
        """
        if self._key is None:
            raise ValueError(
                "Key material could not be obtained from Key Vault. Only remote cryptographic operations "
                "(decrypt, sign) can be performed."
            )

        # Key size only requires public modulus, which we can always get
        # Relying on private numbers instead would cause issues for keys stored in KV (which doesn't return private key)
        return self.public_key().key_size

    def public_key(self) -> KeyVaultRSAPublicKey:
        """The `RSAPublicKey` associated with this private key, as a `KeyVaultRSAPublicKey`.

        The public key implementation will use the same underlying cryptography client as this private key.

        :returns: The `KeyVaultRSAPublicKey` associated with the key.
        :rtype: ~azure.keyvault.keys.crypto.KeyVaultRSAPublicKey
        """
        return KeyVaultRSAPublicKey(self._client, self._key)

    def sign(
        self,
        data: bytes,
        padding: AsymmetricPadding,
        algorithm: Union[Prehashed, HashAlgorithm],
    ) -> bytes:
        """Signs the data.

        :param bytes data: The data to sign, as bytes.
        :param padding: The padding to use. Supported paddings are `PKCS1v15` and `PSS`. For `PSS`, the only supported
            mask generation function is `MGF1`. See https://learn.microsoft.com/azure/key-vault/keys/about-keys-details
            for details.
        :type padding: ~cryptography.hazmat.primitives.asymmetric.padding.AsymmetricPadding
        :param algorithm: The algorithm to sign with. Only `HashAlgorithm`s are supported -- specifically, `SHA256`,
            `SHA384`, and `SHA512`.
        :type algorithm: ~cryptography.hazmat.primitives.asymmetric.utils.Prehashed or
            cryptography.hazmat.primitives.hashes.HashAlgorithm

        :returns: The signature, as bytes.
        :rtype: bytes
        """
        if isinstance(algorithm, Prehashed):
            raise ValueError("`Prehashed` algorithms are unsupported. Please provide a `HashAlgorithm` instead.")
        mapped_algorithm = get_signature_algorithm(padding, algorithm)
        digest = Hash(algorithm)
        digest.update(data)
        result = self._client.sign(mapped_algorithm, digest.finalize())
        return result.signature

    def private_numbers(self) -> RSAPrivateNumbers:
        """Returns an `RSAPrivateNumbers` representing the key's private numbers.

        :returns: The private numbers of the key.
        :rtype: ~cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateNumbers

        :raises ValueError: if the client is unable to obtain the key material from Key Vault.
        """
        if self._key is None:
            raise ValueError(
                "Key material could not be obtained from Key Vault. Only remote cryptographic operations "
                "(decrypt, sign) can be performed."
            )

        # Fetch public numbers from JWK
        e = int.from_bytes(self._key.e, "big")  # type: ignore[attr-defined]
        n = int.from_bytes(self._key.n, "big")  # type: ignore[attr-defined]
        public_numbers = RSAPublicNumbers(e, n)

        # Fetch private numbers from JWK
        p = int.from_bytes(self._key.p, "big") if self._key.p else None  # type: ignore[attr-defined]
        q = int.from_bytes(self._key.q, "big") if self._key.q else None  # type: ignore[attr-defined]
        d = int.from_bytes(self._key.d, "big") if self._key.d else None  # type: ignore[attr-defined]
        dmp1 = int.from_bytes(self._key.dp, "big") if self._key.dp else None  # type: ignore[attr-defined]
        dmq1 = int.from_bytes(self._key.dq, "big") if self._key.dq else None  # type: ignore[attr-defined]
        iqmp = int.from_bytes(self._key.qi, "big") if self._key.qi else None  # type: ignore[attr-defined]

        # Calculate any missing attributes
        if d is None:
            raise ValueError("An 'RSAPrivateNumbers' couldn't be created with the available key material.")
        if p is None or q is None:
            p, q = rsa_recover_prime_factors(n, e, d)
        if dmp1 is None:
            dmp1 = rsa_crt_dmp1(d, p)
        if dmq1 is None:
            dmq1 = rsa_crt_dmq1(d, q)
        if iqmp is None:
            iqmp = rsa_crt_iqmp(p, q)

        return RSAPrivateNumbers(p, q, d, dmp1, dmq1, iqmp, public_numbers)

    def private_bytes(
        self, encoding: Encoding, format: PrivateFormat, encryption_algorithm: KeySerializationEncryption
    ) -> bytes:
        """Allows serialization of the key to bytes.

        This function uses the `cryptography` library's implementation.
        Encoding (`PEM` or `DER`) and format (`TraditionalOpenSSL`, `OpenSSH`, or `PKCS8`) and encryption algorithm
        (such as `BestAvailableEncryption` or `NoEncryption`) are chosen to define the exact serialization.

        :param encoding: A value from the `Encoding` enum.
        :type encoding: ~cryptography.hazmat.primitives.serialization.Encoding
        :param format: A value from the `PrivateFormat` enum.
        :type format: ~cryptography.hazmat.primitives.serialization.PrivateFormat
        :param encryption_algorithm: An instance of an object conforming to the `KeySerializationEncryption` interface.
        :type encryption_algorithm: ~cryptography.hazmat.primitives.serialization.KeySerializationEncryption

        :returns: The serialized key.
        :rtype: bytes

        :raises ValueError: if the client is unable to obtain the key material from Key Vault.
        """
        if self._key is None:
            raise ValueError(
                "Key material could not be obtained from Key Vault. Only remote cryptographic operations "
                "(decrypt, sign) can be performed."
            )

        try:
            private_numbers = self.private_numbers()
        except ValueError as exc:
            raise ValueError("Insufficient key material to serialize the private key.") from exc
        private_key = private_numbers.private_key()
        return private_key.private_bytes(encoding=encoding, format=format, encryption_algorithm=encryption_algorithm)

    def signer(  # pylint:disable=docstring-missing-param,docstring-missing-return,docstring-missing-rtype
        self, padding: AsymmetricPadding, algorithm: HashAlgorithm
    ) -> NoReturn:
        """Not implemented. This method was deprecated in `cryptography` 2.0 and removed in 37.0.0."""
        raise NotImplementedError()

    def __copy__(self) -> KeyVaultRSAPrivateKey:
        """Returns this instance since it is treated as immutable.

        :returns: This instance.
        :rtype: ~azure.keyvault.keys.crypto.KeyVaultRSAPrivateKey
        """
        return self


class DecryptResult:
    """The result of a decrypt operation.

    :param str key_id: The encryption key's Key Vault identifier
    :param algorithm: The encryption algorithm used
    :type algorithm: ~azure.keyvault.keys.crypto.EncryptionAlgorithm
    :param bytes plaintext: The decrypted bytes
    """

    def __init__(self, key_id: Optional[str], algorithm: EncryptionAlgorithm, plaintext: bytes) -> None:
        self.key_id = key_id
        self.algorithm = algorithm
        self.plaintext = plaintext


class EncryptResult:
    """The result of an encrypt operation.

    :param str key_id: The encryption key's Key Vault identifier
    :param algorithm: The encryption algorithm used
    :type algorithm: ~azure.keyvault.keys.crypto.EncryptionAlgorithm
    :param bytes ciphertext: The encrypted bytes

    :keyword bytes iv: Initialization vector for symmetric algorithms
    :keyword bytes authentication_tag: The tag to authenticate when performing decryption with an authenticated
        algorithm
    :keyword bytes additional_authenticated_data: Additional data to authenticate but not encrypt/decrypt when using an
        authenticated algorithm
    """

    def __init__(self, key_id: Optional[str], algorithm: EncryptionAlgorithm, ciphertext: bytes, **kwargs: Any) -> None:
        self.key_id = key_id
        self.algorithm = algorithm
        self.ciphertext = ciphertext
        self.iv = kwargs.pop("iv", None)
        self.tag = kwargs.pop("authentication_tag", None)
        self.aad = kwargs.pop("additional_authenticated_data", None)


class SignResult:
    """The result of a sign operation.

    :param str key_id: The signing key's Key Vault identifier
    :param algorithm: The signature algorithm used
    :type algorithm: ~azure.keyvault.keys.crypto.SignatureAlgorithm
    :param bytes signature:
    """

    def __init__(self, key_id: Optional[str], algorithm: SignatureAlgorithm, signature: bytes) -> None:
        self.key_id = key_id
        self.algorithm = algorithm
        self.signature = signature


class VerifyResult:
    """The result of a verify operation.

    :param str key_id: The signing key's Key Vault identifier
    :param bool is_valid: Whether the signature is valid
    :param algorithm: The signature algorithm used
    :type algorithm: ~azure.keyvault.keys.crypto.SignatureAlgorithm
    """

    def __init__(self, key_id: Optional[str], is_valid: bool, algorithm: SignatureAlgorithm) -> None:
        self.key_id = key_id
        self.is_valid = is_valid
        self.algorithm = algorithm


class UnwrapResult:
    """The result of an unwrap key operation.

    :param str key_id: Key encryption key's Key Vault identifier
    :param algorithm: The key wrap algorithm used
    :type algorithm: ~azure.keyvault.keys.crypto.KeyWrapAlgorithm
    :param bytes key: The unwrapped key
    """

    def __init__(self, key_id: Optional[str], algorithm: KeyWrapAlgorithm, key: bytes) -> None:
        self.key_id = key_id
        self.algorithm = algorithm
        self.key = key


class WrapResult:
    """The result of a wrap key operation.

    :param str key_id: The wrapping key's Key Vault identifier
    :param algorithm: The key wrap algorithm used
    :type algorithm: ~azure.keyvault.keys.crypto.KeyWrapAlgorithm
    :param bytes encrypted_key: The encrypted key bytes
    """

    def __init__(self, key_id: Optional[str], algorithm: KeyWrapAlgorithm, encrypted_key: bytes) -> None:
        self.key_id = key_id
        self.algorithm = algorithm
        self.encrypted_key = encrypted_key
