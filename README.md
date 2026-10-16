# Online Judge (Ujian / Latihan)

Sistem online judge berbasis [QingdaoU OnlineJudge 2.0](https://github.com/QingdaoU/OnlineJudge): backend Django, frontend Vue, PostgreSQL, Redis, dan Judge Server.

Project ini **bukan website statis**. Soal, login, submit, dan penilaian butuh backend + database + judger. Yang bisa dihilangkan adalah **`npm run dev`**: setelah frontend di-build, akses lewat Docker di port **8080**.

## Isi folder

| Folder | Fungsi |
| --- | --- |
| `OJ_Backend` | API Django, admin, exam, nginx di dalam container |
| `OJ_Frontend` | Vue (halaman siswa + admin) |
| `Deploy` | `docker-compose.yml` + data runtime |
| `scripts` | Build frontend production |

## Prasyarat

- Docker Desktop (mode **Linux containers** / WSL2)
- Git
- Node.js hanya jika mau mengubah UI (disarankan Node 16–18; project webpack 3)
- Image Docker judger/backend (di-pull saat pertama kali `docker compose up`)

## Cara jalan tanpa `npm run dev` (disarankan)

1. Build frontend sekali (atau setiap kali mengubah Vue):

   ```powershell
   .\scripts\build-frontend.ps1
   ```

   Skrip ini menjalankan `npm run build` lalu menyalin hasil ke `OJ_Backend/dist`.

2. Nyalakan stack:

   ```powershell
   cd Deploy
   docker compose up -d
   ```

3. Buka **http://localhost:8080**.

   - Siswa: `http://localhost:8080`
   - Admin dosen: **bukan** `/admin` (path itu 404). URL rahasia tercetak saat container start, contoh `docker compose logs oj-backend | findstr Portal`
   - Super admin awal image QDUOJ: `root` / `rootroot` — **ganti segera**

4. Setelah build ulang frontend:

   ```powershell
   cd Deploy
   docker compose restart oj-backend
   ```

`npm run dev` (port **8000**) hanya untuk development UI dengan hot-reload; API tetap di-proxy ke Docker di 8080.

## Development frontend (opsional)

```powershell
cd OJ_Frontend
npm install
$env:NODE_ENV = "development"
npm run build:dll    # sekali, kecuali dependency DLL berubah
$env:TARGET = "http://localhost:8080"
npm run dev          # http://localhost:8000
```

## Pindah device

**Kode** ikut GitHub. **Data ujian** (user, soal, submit, PDF, test case, database) **tidak** ikut Git, karena ada di `Deploy/data/`.

Di device baru:

1. `git clone <url-repo> && cd online-judge`
2. Install Docker Desktop.
3. Salin folder `Deploy/data` dari device lama (USB / drive) ke lokasi yang sama. Tanpa ini, database kosong.
4. `cd Deploy; docker compose up -d`
5. Kalau `OJ_Backend/dist` belum ada: jalankan `.\scripts\build-frontend.ps1` (butuh Node + `npm install`, sekali, saat ada internet).

## Offline

| Yang bisa | Yang tidak |
| --- | --- |
| Setelah image Docker sudah di-pull, stack bisa dijalankan tanpa internet | Clone GitHub / `npm install` / pull image pertama kali butuh internet |
| Browser ke `http://localhost:8080` di komputer yang sama, tanpa `npm run dev` | Tidak bisa jadi file HTML murni yang dibuka double-click |
| Pindah device offline jika Anda copy seluruh folder project **termasuk** `Deploy/data` dan image Docker (`docker save` / `docker load`) | Judger, Postgres, Redis tetap harus berjalan (via Docker) |

Simpan image untuk air-gap (opsional, saat masih online):

```powershell
docker pull redis:4.0-alpine
docker pull postgres:10-alpine
docker pull registry.cn-hongkong.aliyuncs.com/oj-image/judge:1.6.1
docker pull registry.cn-hongkong.aliyuncs.com/oj-image/backend:1.6.1
docker save -o oj-images.tar redis:4.0-alpine postgres:10-alpine registry.cn-hongkong.aliyuncs.com/oj-image/judge:1.6.1 registry.cn-hongkong.aliyuncs.com/oj-image/backend:1.6.1
```

Di device tujuan: `docker load -i oj-images.tar` lalu `docker compose up -d`.

## GitHub

Repo ini menyimpan **kode**. Jangan commit:

- `.venv/`, `node_modules/`
- `Deploy/data/` (database, upload, log)
- password, `secret.key`, `.env`

## Token judger

Di `Deploy/docker-compose.yml`, `TOKEN` (judge) dan `JUDGE_SERVER_TOKEN` (backend) harus **sama**. Ganti `CHANGE_THIS` sebelum dipakai serius.

## Lisensi

Kode asal QingdaoU OnlineJudge / OnlineJudgeFE berlisensi MIT. Modifikasi exam/local mengikuti lisensi yang sama kecuali dinyatakan lain.
