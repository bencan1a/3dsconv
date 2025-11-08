"""Factory for creating conversion services with all dependencies.

This module provides the ServiceFactory class which creates fully configured
ConversionService instances with all required dependencies properly wired together.
This follows the dependency injection pattern and centralizes the complex
object graph construction.
"""

import base64
import hashlib
import os
import zlib

from dsconv.crypto.decryption_service import DecryptionService
from dsconv.crypto.key_derivation import KeyDerivationService
from dsconv.io.binary_reader import BinaryReader
from dsconv.io.binary_writer import BinaryWriter
from dsconv.io.cia_writer import CIAWriter
from dsconv.io.exefs_reader import ExeFSReader
from dsconv.io.ncch_reader import NCCHReader
from dsconv.io.ncsd_reader import NCSDReader
from dsconv.services.conversion_config import ConversionConfig
from dsconv.services.conversion_service import ConversionService
from dsconv.services.progress_reporter import ConsoleProgressReporter, IProgressReporter
from dsconv.validation.hash_validator import HashValidator


class ServiceFactory:
    """Factory for creating conversion services with dependencies.

    This factory is responsible for creating ConversionService instances
    with all required dependencies properly configured and injected. It
    handles:
    - Opening input/output files
    - Creating readers and writers
    - Setting up crypto services if keys are available
    - Configuring validation and progress reporting

    Example:
        >>> service = ServiceFactory.create_conversion_service(
        ...     "game.cci",
        ...     "game.cia",
        ...     config
        ... )
        >>> service.convert(config)
    """

    @staticmethod
    def create_conversion_service(
        input_file: str,
        output_file: str,
        config: ConversionConfig,
    ) -> ConversionService:
        """Create fully configured conversion service.

        This method creates and wires together all the dependencies needed
        for a complete CCI to CIA conversion:
        - Binary readers and writers
        - Format-specific readers (NCSD, NCCH, ExeFS)
        - CIA writer
        - Crypto services (if keys are available)
        - Hash validator
        - Progress reporter

        Args:
            input_file: Path to input CCI file
            output_file: Path to output CIA file
            config: ConversionConfig with all conversion parameters

        Returns:
            Fully configured ConversionService ready for conversion

        Raises:
            FileNotFoundError: If input file doesn't exist
            IOError: If files cannot be opened
        """
        # Validate input file exists
        if not os.path.isfile(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")

        # Create output directory if needed
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Open files
        input_handle = open(input_file, "rb")
        output_handle = open(output_file, "wb")

        # Create readers
        binary_reader = BinaryReader(input_handle)
        ncsd_reader = NCSDReader(binary_reader)
        ncch_reader = NCCHReader(binary_reader)
        exefs_reader = ExeFSReader(binary_reader)

        # Create writers
        binary_writer = BinaryWriter(output_handle)

        # Load certificate chain (retail for now, dev handling TBD)
        certchain = ServiceFactory._load_certchain(config.dev_keys)
        cia_writer = CIAWriter(binary_writer, certchain, config.dev_keys)

        # Create crypto services if key provider is available
        decryption_service = None
        if config.key_provider:
            try:
                from dsconv.crypto.aes_adapter import PyAESAdapter

                orig_key = config.key_provider.get_original_ncch_key()
                key_derivation = KeyDerivationService(orig_key)

                # Create AES cipher factory
                def aes_cipher_factory(key: bytes, counter_value: int):
                    """Factory for creating AES-CTR ciphers."""
                    return PyAESAdapter(key, counter_value)

                decryption_service = DecryptionService(key_derivation, aes_cipher_factory)
            except Exception as e:
                # If key loading fails, continue without decryption
                # (will fail later if encrypted content is encountered)
                if config.verbose:
                    print(f"Warning: Could not load encryption keys: {e}")

        # Create validator
        hash_validator = HashValidator(config.ignore_bad_hashes)

        # Create progress reporter
        progress_reporter: IProgressReporter = ConsoleProgressReporter(config.verbose)

        return ConversionService(
            ncsd_reader=ncsd_reader,
            ncch_reader=ncch_reader,
            exefs_reader=exefs_reader,
            cia_writer=cia_writer,
            decryption_service=decryption_service,
            hash_validator=hash_validator,
            progress_reporter=progress_reporter,
        )

    @staticmethod
    def _load_certchain(dev_keys: bool = False) -> bytes:
        """Load certificate chain for CIA signing.

        Args:
            dev_keys: If True, load dev certchain; otherwise retail

        Returns:
            Certificate chain bytes (0xA00 bytes)

        Raises:
            FileNotFoundError: If dev certchain is requested but not found
        """
        if dev_keys:
            # Try to load dev certchain from common locations
            dev_paths = [
                "certchain-dev.bin",
                os.path.expanduser("~/.3ds/certchain-dev.bin"),
            ]

            for path in dev_paths:
                if os.path.isfile(path):
                    with open(path, "rb") as f:
                        certchain = f.read(0xA00)
                        # Validate MD5 hash
                        correct_hash = "d5c3d811a7eb87340aa9f4ab1841b6c4"
                        if hashlib.md5(certchain).hexdigest() == correct_hash:
                            return certchain

            raise FileNotFoundError(
                "Dev certchain not found or invalid. "
                "Place certchain-dev.bin in current directory or ~/.3ds/"
            )
        else:
            # Return retail certchain (embedded)
            # Retail certchain compressed and base64-encoded
            certchain_retail = b"""
eJytkvk/E44fx9GsT58ZsrlvaUmxMJ8RQiTXx50wRRbmWObKkTnTZ5FQxsxNJlfKyvGNCpnJbY7k
+Nacc205P+X69H30+Qv0fb5/fr0er8f78eTi5jqCM9Riv24u8iXhx7jVsVIZzqaWhOJ7kuklQk6R
8/xbJ6Lb+QXVJ7QnF8iZTxecR31JlPlpX759zbNPH/PGIw4S9Lt0jsTJFIDfjZXCYy+9rP1mKOld
KmX8iv1g/s7IsF/ZVURRInZu6M0Io/hiBz1CEqGAvO4aRn57FH6byC7cRnUlhBe08evPdCc8kgs3
QN8369giOLrdzAkZ0UtxOqj+dFWG6HDRDyK2a3I/YYhe6pEMrNu9ZhMFmS9KarGVqRtRLTVOTbCB
Xi6voS63punmDcMfKXdWjbOdaDxipmO35P5SZwyMjS0ag9M9pCKzxwlG7bmyqmfxOVfxtmdFsAHR
EtXmYeZI4+jwfTn5L+bEAaFCTHWh+Aa6o9QxseI1htCoeDNhIDk3NuCymZiGaDzC3CJRTcMCdk4d
PTa4ZG3RmMlDtdt6ZmBCI1+Pfmguxs55Vzw1AhE0xAntxVu2iPTVv2/ZXg4MKwox6ZrKXF/5mNrD
CwcRki7t1ZxBQxw2wCKz33PPWn0izZMGrrubTNij14/5nXWPzEsZRgnzUKrwuvSP7aHZD/ERPoJ0
wHviCZurLJkeGLKz5a6tbZUfGZD27AJtI8ygcBxUgj3q7Ng7r2lVwnqyFgSCXeHDaxspNvHVs9Tw
SfdubMinHwg+j3fs1R9EhVy3zUjz+/NGl6Uq1y9gFxAQ8iv5H3AbGZ77icbhCu4ssP1rIzqZq1/k
aYsb1lvaf6ceTbYIWykguj/XjI97xX+lMui4cFEYTjfy3P55FlvKvUk6y+R27XlMN+AFyQ7Vifkq
zRy3mRmb5wTOenxiHlPQYDHQW9KjLQXrT8plUj3thwIn79xt/NrQG6zJ2XTgRRctNmijP+ewuLll
sx3QN5RwcqxucKVpDBTsBStKwJ46LiuHmbocBE237fOhSVL4v42ZFW7LOmSvMciDD3C8iPjH79UO
mjW2mijgDvHrxU3tWDlQDRbYn2s4nsLqkBO2fJJwxufdA58enaPnudDucBMVjdgbpYv+6a7DHpoR
bUs3e43ZTljofyoICO6cC0urjAgu7h93qO9zAdLz35iY92/a9UgGzRPMBPuulHNUbcIzDT9mYvTe
8Tb/vvjX0byk1ru0UKBbCP0tkh5rbEDkKVQggRqqTbX0sUpledOZsO7aWmUB8RlBdU4GtYADUTOZ
om+1lA+7DqbkS12mDshaO8BaO2IhLqdCGR+8czoWEJzPO05zBPcyyLldYoToY/pOuWYZJS1VIW9V
mY/SWKsjNESk7Iv3j8JM5THh7i5e9ilvkZjstGuIS7uuQZH8kM9MepZU7nd/d29CaLCyVaidHtwR
LlTRLBz8Fthp4PDse1wZVLSGbA7ECuy6jFhUKr04cPeSNUYO5cuAM4SWLD70We75In67GxF/OOt+
8j//VX5NYG4n+3/j6MNtgET+llFtg6qjRauiJn11lo3GBDuCWN2nwaWJhHp893EMiMossKp8DWM9
gHGTXAGSL4zC5+6LSVSH8WJYSsWNcd6rFwT7g96wZYvhxRUXIF9lxP4oV74Yx8ZVbMx4ZMfL03Ya
m/tF56qcARms3vLE3CUVZUtRr7U2baH2VOjTI9MB3RPdE5C9yPmoyPCxrLmqtitXPzNYSzdf6j7a
aAd7U3imqOnPvW70qBNAI2ZCNVJN9SLKQM5JT8bz5Znd5clnSWaI8YdzMedESR7ywtcgUv76xyrF
L7UCq3CdF6kBZkViOj3hdTMvo/xdqwRSPP7OohH1BuBK9Xwo/LZtHJmE8ISd/BX/VSn+Xn3rmhF4
QFZ9pHhMwazEqyeQ0IngvXyQoFeOJBkVnVSbyl13x8OhxbxIAyq2hio147JEpozC+eZ0ZHHpFfta
x+qr/JVuU6Tdbf2NKMjTIipKIKbkAnOfF/+wjglQVLgULFG3P81vr4m8sFSOG1Z7XdyloJJ5Vwvv
piy5bcfVC3ScTusVh6Ccv1gLlLYoSQTf6x6gL+tX43Z6Q6ZWZfvdTDRAtt/q86XHN6b1oYQ8XqXT
iu2bE6e82MBTo6sTwbe8W2cbtRBesUHyWKnwhhOFQQzr9eVvzceLyV/9NZqP1dSO/mlvxRMlrgh2
dsEsUXmr3ptTkxrkaEMwR77DWfeT/4f/Rjb/xj0Ot+GH/yDK/fa0PRAcbO1Yp77z2Ko/mChKPR8x
BeBnqbRJIzu2dTgWjBkruUqXgMVNkmXLFlCVXDDrr544EXBycrj/bQGTvaD5Xxhi5XFMJQ90ABCb
u21xj98PkLDRo1KpnMnT5MgZac7wXbkFmuGkwjB+/fnb4+pu8S9SfddW7FB78cme+qu3eg3ALqYH
TBX75FcaKEN7hIqRZtVmWj/jdyZAN8ZlELqbKzD33aCU7gn8gPZpWjUuUcn3ceWArEfJ444p0Fw5
pSLLvMAGmw9/oJDbIM+w9N1rQQ+sxPYUrkQZeIxeDrTXxYnm6T1LffRCdMaVqr5ObS1Wxbnu0wKw
JWFnDuv/P7kyh1k="""
            return zlib.decompress(base64.b64decode(certchain_retail))
