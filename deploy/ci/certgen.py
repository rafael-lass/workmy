"""Disposable test certificates using the backend's locked cryptography."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

folder = Path(__file__).resolve().parent
certs = folder / 'certs'
certs.mkdir(exist_ok=True)
for name, hostname in [('server', 'postgres'), ('web', 'localhost')]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, hostname)])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5)).not_valid_after(now + timedelta(days=2))
            .add_extension(x509.SubjectAlternativeName([x509.DNSName(hostname)]), critical=False)
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .sign(key, hashes.SHA256()))
    (certs / f'{name}.key').write_bytes(key.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    (certs / f'{name}.crt').write_bytes(cert.public_bytes(serialization.Encoding.PEM))
certificate = (certs / 'server.crt').read_text()
(folder / '.env').write_text("DATABASE_CA_CERT='" + certificate + "'\n", encoding='utf-8')
