import pandas as pd
from datetime import datetime
from app.models.distribusi import Distribusi
from app.extensions import db

class DistribusiService:
    @staticmethod
    def baca_file_excel(file_path_or_stream):
        try:
            df = pd.read_excel(file_path_or_stream)
            return df
        except Exception as e:
            raise ValueError(f"Gagal membaca file Excel: {str(e)}")

    @staticmethod
    def validasi_format_data(df):
        if df.empty:
            raise ValueError("File Excel kosong / tidak memiliki baris data.")

        date_col = None
        val_col = None
        
        for c in df.columns:
            c_lower = str(c).strip().lower()
            if any(k in c_lower for k in ['periode', 'tanggal', 'bulan', 'date', 'month']):
                date_col = c
                break
                
        for c in df.columns:
            c_lower = str(c).strip().lower()
            if any(k in c_lower for k in ['jumlah', 'distribusi', 'volume', 'qty', 'kg', 'value', 'amount']):
                val_col = c
                break
                
        if not date_col or not val_col:
            raise ValueError("File Excel harus memiliki kolom Periode (Tanggal/Bulan) dan Jumlah Distribusi (kg).")
            
        clean_df = pd.DataFrame()
        
        try:
            # Convert to datetime and set day to 1
            parsed_dates = pd.to_datetime(df[date_col], errors='coerce')
            if parsed_dates.isnull().all():
                raise ValueError("Format tanggal pada kolom Periode tidak dikenali.")
            clean_df['periode'] = parsed_dates.dt.to_period('M').dt.to_timestamp()
        except Exception as e:
            raise ValueError(f"Gagal memproses kolom tanggal/periode: {str(e)}")
            
        try:
            clean_df['jumlah_distribusi'] = pd.to_numeric(df[val_col], errors='coerce').astype(int)
        except Exception as e:
            raise ValueError(f"Gagal memproses kolom jumlah distribusi: {str(e)}")
            
        if clean_df['periode'].isnull().any():
            raise ValueError("Terdapat baris data dengan periode/tanggal kosong.")
            
        if clean_df['jumlah_distribusi'].isnull().any():
            raise ValueError("Terdapat baris data dengan jumlah distribusi kosong atau non-numerik.")
            
        if (clean_df['jumlah_distribusi'] <= 0).any():
            raise ValueError("Jumlah distribusi harus bernilai lebih dari 0.")
            
        # Drop duplicates in excel
        clean_df = clean_df.drop_duplicates(subset=['periode'])
        
        # Check minimal 12 bulan (1 tahun penuh)
        n_bulan = clean_df['periode'].nunique()
        if n_bulan < 12:
            raise ValueError(
                f"Data yang diimport harus minimal 1 tahun (12 bulan penuh). "
                f"File yang diupload hanya berisi {n_bulan} bulan."
            )
        
        return clean_df

    @staticmethod
    def simpan_ke_database(clean_df, id_user):
        # Collect all dates from Excel
        dates = clean_df['periode'].dt.date.tolist()
        
        # Check for duplicates in database
        existing_records = Distribusi.query.filter(
            Distribusi.periode_tanggal.in_(dates)
        ).all()
        
        if existing_records:
            duplicate_periods = sorted([
                r.periode_tanggal.strftime('%Y-%m') for r in existing_records
            ])
            raise ValueError(
                f"Periode berikut sudah terdaftar di database: "
                f"{', '.join(duplicate_periods)}. "
                f"Hapus data yang sudah ada terlebih dahulu jika ingin menggantinya."
            )
        
        # Insert new records
        records_added = 0
        for idx, row in clean_df.iterrows():
            new_dist = Distribusi(
                periode_tanggal=row['periode'].date(),
                jumlah_distribusi=int(row['jumlah_distribusi']),
                id_user=id_user
            )
            db.session.add(new_dist)
            records_added += 1
                
        db.session.commit()
        return records_added

    @staticmethod
    def update_data(periode_str, jumlah_baru):
        if jumlah_baru <= 0:
            raise ValueError("Jumlah distribusi harus lebih dari 0.")
        try:
            target_date = pd.to_datetime(periode_str).date().replace(day=1)
        except Exception as e:
            raise ValueError(f"Format periode tidak valid: {str(e)}")
        record = Distribusi.query.filter_by(periode_tanggal=target_date).first()
        if not record:
            raise ValueError(f"Data untuk periode {periode_str} tidak ditemukan.")
        record.jumlah_distribusi = int(jumlah_baru)
        db.session.commit()
        return True

    @staticmethod
    def get_all_data():
        return Distribusi.query.order_by(Distribusi.periode_tanggal.asc()).all()

    @staticmethod
    def delete_data(periode_str):
        try:
            target_date = pd.to_datetime(periode_str).date()
            target_date = target_date.replace(day=1)
        except Exception as e:
            raise ValueError(f"Format periode tidak valid: {str(e)}")
            
        record = Distribusi.query.filter_by(periode_tanggal=target_date).first()
        if not record:
            raise ValueError(f"Data untuk periode {periode_str} tidak ditemukan.")
            
        db.session.delete(record)
        db.session.commit()
        return True

    @staticmethod
    def delete_by_year(tahun):
        try:
            year_int = int(tahun)
        except ValueError:
            raise ValueError("Tahun tidak valid.")
        start_date = pd.Timestamp(year=year_int, month=1, day=1).date()
        end_date = pd.Timestamp(year=year_int, month=12, day=31).date()
        records = Distribusi.query.filter(
            Distribusi.periode_tanggal >= start_date,
            Distribusi.periode_tanggal <= end_date
        ).all()
        if not records:
            raise ValueError(f"Tidak ada data untuk tahun {tahun}.")
        for rec in records:
            db.session.delete(rec)
        db.session.commit()
        return len(records)
