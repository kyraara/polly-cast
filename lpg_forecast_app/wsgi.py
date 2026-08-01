import os
from dotenv import load_dotenv

# Load environment variables from .env
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Harus di-set sebelum numpy diimpor. Secara default OpenBLAS membuka thread
# sebanyak jumlah core; pada shared hosting yang membatasi jumlah proses
# (RLIMIT_NPROC) hal ini membuat startup sangat lambat atau gagal.
for _var in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS',
             'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ.setdefault(_var, '1')

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run()
