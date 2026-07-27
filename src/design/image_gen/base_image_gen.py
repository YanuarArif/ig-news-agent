"""Interface abstrak untuk semua image generator (mock, stability, dll).
Sama pola dengan BasePublisher — supaya provider bisa ditukar tanpa
mengubah kode compositor.py."""

from abc import ABC, abstractmethod


class BaseImageGen(ABC):
    @abstractmethod
    def generate(self, prompt: str, output_path: str) -> str:
        """Generate 1 gambar background dari prompt, simpan ke output_path.

        Returns:
            path file gambar yang dihasilkan (sama dengan output_path).
        """
        raise NotImplementedError