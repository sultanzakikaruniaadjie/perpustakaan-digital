"""
APLIKASI PERPUSTAKAAN DIGITAL
Kelompok 2: Sultan Zaki dan Zulfa
Database: Supabase (PostgreSQL)
Jalankan: python -m streamlit run app_supabase.py
"""

import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta

st.set_page_config(page_title="Perpustakaan Digital", page_icon="📚",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stat-card { background:#1C2333; border:1px solid #30363D; border-radius:12px; padding:20px; text-align:center; }
.stat-nilai { font-size:2rem; font-weight:bold; }
.stat-label { color:#8B949E; font-size:0.85rem; margin-top:4px; }
.badge-admin   { background:#7C3AED22; color:#A78BFA; padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }
.badge-peminjam{ background:#2563EB22; color:#60A5FA; padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ── KONEKSI SUPABASE ─────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def db():
    return get_supabase()

# ── HELPER DB ────────────────────────────────────────────────────
def get_buku(keyword=""):
    data = db().table("buku").select("*").order("id").execute().data or []
    if keyword:
        kw = keyword.lower()
        data = [b for b in data if kw in b["judul"].lower() or kw in b["pengarang"].lower()]
    return data

def get_users():
    data = db().table("users").select("*").execute().data or []
    return {u["username"]: u for u in data}

def get_semua_pinjam():
    return db().table("peminjaman").select("*").order("id").execute().data or []

def get_pinjam_aktif():
    return db().table("peminjaman").select("*").eq("status","dipinjam").execute().data or []

def get_pinjam_user(username):
    return db().table("peminjaman").select("*").eq("username",username).execute().data or []

def cek_terlambat(tgl):
    return max(0, (datetime.now() - datetime.strptime(tgl, "%Y-%m-%d")).days)

def statistik():
    buku = get_buku(); pinjam = get_semua_pinjam()
    return {
        "total_buku":  len(buku),
        "total_stok":  sum(b["stok"] for b in buku),
        "aktif":       sum(1 for p in pinjam if p["status"]=="dipinjam"),
        "kembali":     sum(1 for p in pinjam if p["status"]=="dikembalikan"),
        "terlambat":   sum(1 for p in pinjam if p["status"]=="dipinjam" and cek_terlambat(p["tgl_kembali"])>0),
    }

# ── SESSION ──────────────────────────────────────────────────────
def init_session():
    for k,v in [("logged_in",False),("current_user",None),
                ("current_role",None),("current_nama",None),("halaman","dashboard")]:
        if k not in st.session_state: st.session_state[k]=v

# ── LOGIN ────────────────────────────────────────────────────────
def halaman_login():
    st.markdown("<br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1,1.2,1])
    with col:
        st.markdown("## 📚 Perpustakaan Digital Poltek META")
        st.markdown("**Kelompok 2 — Sultan Zaki & Zulfa**")
        st.markdown("---")
        tab1, tab2 = st.tabs(["🔑 Login","📝 Daftar Akun"])

        with tab1:
            with st.form("form_login"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit   = st.form_submit_button("Masuk →", use_container_width=True, type="primary")
            if submit:
                res = db().table("users").select("*").eq("username",username).execute().data or []
                if res and res[0]["password"]==password:
                    u=res[0]
                    st.session_state.update(logged_in=True, current_user=username,
                                            current_role=u["role"], current_nama=u["nama"], halaman="dashboard")
                    st.rerun()
                else:
                    st.error("❌ Username atau password salah!")
            st.markdown("---")
            st.caption("Demo: admin/admin123  •  zaki/zaki123  •  zulfa/zulfa123")

        with tab2:
            with st.form("form_daftar"):
                nama_baru=st.text_input("Nama Lengkap"); user_baru=st.text_input("Username")
                pass_baru=st.text_input("Password",type="password")
                ok=st.form_submit_button("Daftar Sekarang",use_container_width=True,type="primary")
            if ok:
                if not all([nama_baru,user_baru,pass_baru]): st.error("Semua field wajib diisi!")
                elif db().table("users").select("username").eq("username",user_baru).execute().data:
                    st.error("Username sudah dipakai!")
                else:
                    db().table("users").insert({"username":user_baru,"password":pass_baru,
                                                "nama":nama_baru,"role":"peminjam"}).execute()
                    st.success(f"✅ Akun '{user_baru}' berhasil dibuat!")

# ── SIDEBAR ──────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("## 📚 Perpustakaan Poltek META"); st.markdown("---")
        role=st.session_state.current_role; nama=st.session_state.current_nama
        st.markdown(f"**{nama}**")
        st.markdown(f'<span class="badge-{"admin" if role=="admin" else "peminjam"}">● {role.capitalize()}</span>', unsafe_allow_html=True)
        st.markdown("---")
        menus=([("dashboard","🏠 Dashboard"),("buku","📖 Koleksi Buku"),("tambah_buku","➕ Tambah Buku"),
                ("peminjaman","📋 Peminjaman Aktif"),("pengembalian","↩️ Pengembalian"),
                ("riwayat","🕒 Semua Riwayat"),("member","👥 Data Member")]
               if role=="admin" else
               [("dashboard","🏠 Dashboard"),("buku","📖 Koleksi Buku"),("pinjam","🔖 Pinjam Buku"),
                ("kembalikan","↩️ Kembalikan Buku"),("riwayat_saya","🕒 Riwayat Saya"),
                ("riwayat","📋 Semua Riwayat")])
        for key,label in menus:
            if st.button(label,key=f"nav_{key}",use_container_width=True,
                         type="primary" if st.session_state.halaman==key else "secondary"):
                st.session_state.halaman=key; st.rerun()
        st.markdown("---")
        if st.button("🚪 Logout",use_container_width=True):
            st.session_state.update(logged_in=False,current_user=None,current_role=None,
                                    current_nama=None,halaman="dashboard"); st.rerun()

# ── TABEL BUKU ───────────────────────────────────────────────────
def _tabel_buku(keyword=""):
    data=get_buku(keyword)
    if not data: st.info("Tidak ada buku ditemukan."); return
    st.dataframe([{"ID":b["id"],"Judul":b["judul"],"Pengarang":b["pengarang"],
                   "Genre":b["genre"],"Tahun":b["tahun"],
                   "Stok":f"✅ {b['stok']}" if b["stok"]>0 else "❌ Habis"} for b in data],
                 use_container_width=True, hide_index=True)

# ── DASHBOARD ────────────────────────────────────────────────────
def hal_dashboard():
    role=st.session_state.current_role; nama=st.session_state.current_nama
    st.title("🛡️ Panel Admin" if role=="admin" else f"👋 Halo, {nama}!")
    st.caption(f"Perpustakaan Digital  •  {datetime.now().strftime('%A, %d %B %Y')}")
    st.markdown("---")
    stat=statistik()
    for col,(nilai,label,warna,ikon) in zip(st.columns(5),[
        (stat["total_buku"],"Judul Buku","#60A5FA","📚"),
        (stat["total_stok"],"Total Stok","#A78BFA","🗂️"),
        (stat["aktif"],"Sedang Dipinjam","#FBBF24","🔖"),
        (stat["terlambat"],"Terlambat","#F87171","⚠️"),
        (stat["kembali"],"Sudah Kembali","#34D399","✅"),
    ]):
        with col:
            st.markdown(f'<div class="stat-card"><div style="font-size:1.8rem">{ikon}</div>'
                        f'<div class="stat-nilai" style="color:{warna}">{nilai}</div>'
                        f'<div class="stat-label">{label}</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📖 Koleksi Buku"); _tabel_buku()

# ── KOLEKSI BUKU ─────────────────────────────────────────────────
def hal_buku():
    st.title("📖 Koleksi Buku"); st.markdown("---")
    _tabel_buku(st.text_input("🔍 Cari judul atau pengarang..."))

# ── TAMBAH BUKU (ADMIN) ──────────────────────────────────────────
def hal_tambah_buku():
    st.title("➕ Tambah / Kelola Buku"); st.markdown("---")
    cf, ct = st.columns([1,1.6])
    with cf:
        st.subheader("Tambah Buku Baru")
        with st.form("form_tambah", clear_on_submit=True):
            judul=st.text_input("Judul Buku *"); pengarang=st.text_input("Pengarang *")
            genre=st.text_input("Genre"); c1,c2=st.columns(2)
            tahun=c1.number_input("Tahun",min_value=1900,max_value=2030,value=2024)
            stok=c2.number_input("Stok *",min_value=1,value=1)
            submit=st.form_submit_button("➕ Tambah Buku",use_container_width=True,type="primary")
        if submit:
            if not judul or not pengarang: st.error("Judul dan pengarang wajib diisi!")
            else:
                db().table("buku").insert({"judul":judul,"pengarang":pengarang,
                    "genre":genre or "Umum","tahun":int(tahun),"stok":int(stok)}).execute()
                st.success(f"✅ '{judul}' berhasil ditambahkan!"); st.rerun()
    with ct:
        st.subheader("Buku Saat Ini")
        data=get_buku()
        st.dataframe([{"ID":b["id"],"Judul":b["judul"],"Pengarang":b["pengarang"],"Stok":b["stok"]}
                      for b in data], use_container_width=True, hide_index=True)
        if data:
            pilihan={str(b["id"]):f"{b['id']} — {b['judul']}" for b in data}
            id_h=st.selectbox("Hapus buku",list(pilihan.keys()),format_func=lambda x:pilihan[x])
            if st.button("🗑️ Hapus",type="secondary"):
                if db().table("peminjaman").select("id").eq("id_buku",int(id_h)).eq("status","dipinjam").execute().data:
                    st.error("❌ Buku sedang dipinjam!")
                else:
                    db().table("buku").delete().eq("id",int(id_h)).execute()
                    st.success("✅ Buku dihapus."); st.rerun()
            pilihan2={str(b["id"]):f"{b['id']} — {b['judul']} (stok:{b['stok']})" for b in data}
            id_u=st.selectbox("Update stok",list(pilihan2.keys()),format_func=lambda x:pilihan2[x],key="upd")
            stok_baru=st.number_input("Stok baru",min_value=0,value=1)
            if st.button("💾 Update Stok"):
                db().table("buku").update({"stok":int(stok_baru)}).eq("id",int(id_u)).execute()
                st.success("✅ Stok diperbarui!"); st.rerun()

# ── PEMINJAMAN AKTIF (ADMIN) ─────────────────────────────────────
def hal_peminjaman_aktif():
    st.title("📋 Peminjaman Aktif"); st.markdown("---")
    aktif=get_pinjam_aktif()
    if not aktif: st.info("Tidak ada peminjaman aktif."); return
    buku_map={b["id"]:b["judul"] for b in get_buku()}
    usr_map={u:d["nama"] for u,d in get_users().items()}
    rows=[]
    for p in aktif:
        t=cek_terlambat(p["tgl_kembali"])
        rows.append({"ID":p["id"],"Peminjam":usr_map.get(p["username"],p["username"]),
                     "Buku":buku_map.get(p["id_buku"],""),"Tgl Pinjam":p["tgl_pinjam"],
                     "Tgl Kembali":p["tgl_kembali"],
                     "Status":f"⚠️ Terlambat {t} hari" if t>0 else "✅ Tepat waktu",
                     "Denda":f"Rp {t*1000:,}" if t>0 else "-"})
    st.metric("Total Aktif",len(aktif))
    st.dataframe(rows,use_container_width=True,hide_index=True)

# ── PENGEMBALIAN (ADMIN) ─────────────────────────────────────────
def hal_pengembalian():
    st.title("↩️ Proses Pengembalian"); st.markdown("---")
    aktif=get_pinjam_aktif()
    if not aktif: st.info("Tidak ada peminjaman aktif."); return
    buku_map={b["id"]:b["judul"] for b in get_buku()}
    usr_map={u:d["nama"] for u,d in get_users().items()}
    opsi={str(p["id"]):f"{p['id']} — {usr_map.get(p['username'],'')} — {buku_map.get(p['id_buku'],'')}" for p in aktif}
    pid=st.selectbox("Pilih peminjaman",list(opsi.keys()),format_func=lambda x:opsi[x])
    if pid:
        p=next(x for x in aktif if str(x["id"])==pid)
        t=cek_terlambat(p["tgl_kembali"]); denda=t*1000
        c1,c2=st.columns(2)
        c1.info(f"**Peminjam:** {usr_map.get(p['username'],'')}\n\n**Buku:** {buku_map.get(p['id_buku'],'')}\n\n**Batas:** {p['tgl_kembali']}")
        if t>0: c2.error(f"⚠️ Terlambat **{t} hari**\n\nDenda: **Rp {denda:,}**")
        else: c2.success("✅ Tepat waktu! Tidak ada denda.")
        if st.button("↩️ Proses Pengembalian",type="primary",use_container_width=True):
            db().table("peminjaman").update({"status":"dikembalikan",
                "tgl_dikembalikan":datetime.now().strftime("%Y-%m-%d")}).eq("id",int(pid)).execute()
            stok_lama=db().table("buku").select("stok").eq("id",p["id_buku"]).execute().data[0]["stok"]
            db().table("buku").update({"stok":stok_lama+1}).eq("id",p["id_buku"]).execute()
            st.success(f"✅ Berhasil dikembalikan!" + (f" Denda: Rp {denda:,}" if denda else "")); st.rerun()

# ── RIWAYAT SEMUA (ADMIN) ────────────────────────────────────────
def hal_riwayat_semua():
    st.title("🕒 Semua Riwayat Peminjaman"); st.markdown("---")
    semua=get_semua_pinjam()
    if not semua: st.info("Belum ada riwayat."); return
    buku_map={b["id"]:b["judul"] for b in get_buku()}
    usr_map={u:d["nama"] for u,d in get_users().items()}
    rows=[{"ID":p["id"],"Peminjam":usr_map.get(p["username"],p["username"]),
           "Buku":buku_map.get(p["id_buku"],""),"Tgl Pinjam":p["tgl_pinjam"],
           "Batas Kembali":p["tgl_kembali"],
           "Tgl Dikembalikan":p["tgl_dikembalikan"] if p["tgl_dikembalikan"] else "-",
           "Status":"✅ Dikembalikan" if p["status"]=="dikembalikan" else "⏳ Aktif"}
          for p in semua]
    c1,c2=st.columns(2); c1.metric("Total",len(rows)); c2.metric("Aktif",sum(1 for r in rows if r["Status"]=="⏳ Aktif"))
    st.dataframe(rows,use_container_width=True,hide_index=True)

# ── DATA MEMBER (ADMIN) ──────────────────────────────────────────
def hal_member():
    st.title("👥 Data Member"); st.markdown("---")
    users=get_users(); semua=get_semua_pinjam()
    rows=[{"Username":u,"Nama":d["nama"],
           "Pinjam Aktif":sum(1 for p in semua if p["username"]==u and p["status"]=="dipinjam"),
           "Total Pinjam":sum(1 for p in semua if p["username"]==u)}
          for u,d in users.items() if d["role"]!="admin"]
    st.metric("Total Member",len(rows)); st.dataframe(rows,use_container_width=True,hide_index=True)

# ── PINJAM BUKU (PEMINJAM) ───────────────────────────────────────
def hal_pinjam():
    st.title("🔖 Pinjam Buku"); st.caption("Batas: 7 hari  •  Denda: Rp 1.000/hari"); st.markdown("---")
    username=st.session_state.current_user
    _tabel_buku(st.text_input("🔍 Cari buku..."))
    st.markdown("---"); st.subheader("Pilih Buku")
    tersedia=[b for b in get_buku() if b["stok"]>0]
    if not tersedia: st.warning("Semua buku habis stok."); return
    pilihan={str(b["id"]):f"{b['id']} — {b['judul']} ({b['pengarang']})" for b in tersedia}
    bid=st.selectbox("Pilih buku",list(pilihan.keys()),format_func=lambda x:pilihan[x])
    if bid:
        b=next(x for x in tersedia if str(x["id"])==bid)
        tgl_p=datetime.now(); tgl_k=tgl_p+timedelta(days=7)
        c1,c2=st.columns(2)
        c1.info(f"**Buku:** {b['judul']}\n\n**Pengarang:** {b['pengarang']}\n\n**Stok:** {b['stok']}")
        c2.info(f"**Tgl Pinjam:** {tgl_p.strftime('%d %B %Y')}\n\n**Batas:** {tgl_k.strftime('%d %B %Y')}")
        if db().table("peminjaman").select("id").eq("username",username).eq("id_buku",int(bid)).eq("status","dipinjam").execute().data:
            st.warning("⚠️ Kamu sudah meminjam buku ini.")
        elif st.button("🔖 Pinjam Sekarang",type="primary",use_container_width=True):
            db().table("peminjaman").insert({"username":username,"id_buku":int(bid),
                "tgl_pinjam":tgl_p.strftime("%Y-%m-%d"),"tgl_kembali":tgl_k.strftime("%Y-%m-%d"),
                "status":"dipinjam","tgl_dikembalikan":None}).execute()
            db().table("buku").update({"stok":b["stok"]-1}).eq("id",int(bid)).execute()
            st.success(f"✅ Berhasil meminjam '{b['judul']}'!"); st.rerun()

# ── KEMBALIKAN BUKU (PEMINJAM) ───────────────────────────────────
def hal_kembalikan():
    st.title("↩️ Kembalikan Buku"); st.markdown("---")
    username=st.session_state.current_user
    milik=[p for p in get_pinjam_user(username) if p["status"]=="dipinjam"]
    if not milik: st.info("Tidak sedang meminjam buku apapun."); return
    buku_map={b["id"]:b["judul"] for b in get_buku()}
    rows=[{"ID":p["id"],"Buku":buku_map.get(p["id_buku"],""),"Batas":p["tgl_kembali"],
           "Status":f"⚠️ Terlambat {cek_terlambat(p['tgl_kembali'])} hari" if cek_terlambat(p["tgl_kembali"])>0 else "✅ Tepat waktu",
           "Denda":f"Rp {cek_terlambat(p['tgl_kembali'])*1000:,}" if cek_terlambat(p["tgl_kembali"])>0 else "-",
           "Tgl Kembali":p["tgl_kembali"]} for p in milik]
    st.dataframe(rows,use_container_width=True,hide_index=True); st.markdown("---")
    opsi={str(p["id"]):f"{p['id']} — {buku_map.get(p['id_buku'],'')}" for p in milik}
    pid=st.selectbox("Pilih buku yang dikembalikan",list(opsi.keys()),format_func=lambda x:opsi[x])
    if pid:
        p=next(x for x in milik if str(x["id"])==pid)
        t=cek_terlambat(p["tgl_kembali"]); denda=t*1000
        if t>0: st.error(f"⚠️ Terlambat {t} hari — Denda: **Rp {denda:,}**")
        else: st.success("✅ Tepat waktu!")
        if st.button("↩️ Kembalikan Sekarang",type="primary",use_container_width=True):
            db().table("peminjaman").update({"status":"dikembalikan",
                "tgl_dikembalikan":datetime.now().strftime("%Y-%m-%d")}).eq("id",int(pid)).execute()
            stok_lama=db().table("buku").select("stok").eq("id",p["id_buku"]).execute().data[0]["stok"]
            db().table("buku").update({"stok":stok_lama+1}).eq("id",p["id_buku"]).execute()
            st.success("✅ Berhasil dikembalikan!" + (f" Denda Rp {denda:,} harap dibayar." if denda else "")); st.rerun()

# ── RIWAYAT SAYA (PEMINJAM) ──────────────────────────────────────
def hal_riwayat_saya():
    st.title("🕒 Riwayat Pinjam Saya"); st.caption(f"Akun: {st.session_state.current_nama}"); st.markdown("---")
    username=st.session_state.current_user
    riwayat=get_pinjam_user(username)
    if not riwayat: st.info("Belum ada riwayat."); return
    buku_map={b["id"]:b["judul"] for b in get_buku()}
    rows=[]
    for p in riwayat:
        t=cek_terlambat(p["tgl_kembali"])
        status=("✅ Dikembalikan" if p["status"]=="dikembalikan"
                else f"⚠️ Terlambat {t} hari" if t>0 else "⏳ Sedang dipinjam")
        rows.append({"ID":p["id"],"Buku":buku_map.get(p["id_buku"],""),
                     "Tgl Pinjam":p["tgl_pinjam"],
                     "Tgl Kembali":p["tgl_kembali"],
                     "Tgl Dikembalikan":p["tgl_dikembalikan"] if p["tgl_dikembalikan"] else "-",
                     "Status":status})
    c1,c2=st.columns(2); c1.metric("Total Pinjam",len(rows))
    c2.metric("Masih Aktif",sum(1 for r in rows if "dipinjam" in r["Status"] or "Terlambat" in r["Status"]))
    st.dataframe(rows,use_container_width=True,hide_index=True)

# ── MAIN ─────────────────────────────────────────────────────────
def main():
    init_session()
    if not st.session_state.logged_in: halaman_login(); return
    render_sidebar()
    h=st.session_state.halaman; role=st.session_state.current_role
    admin_only={"tambah_buku","peminjaman","pengembalian","member"}
    peminjam_only={"pinjam","kembalikan","riwayat_saya"}
    routes={"dashboard":hal_dashboard,"buku":hal_buku,"tambah_buku":hal_tambah_buku,
            "peminjaman":hal_peminjaman_aktif,"pengembalian":hal_pengembalian,
            "riwayat":hal_riwayat_semua,"member":hal_member,
            "pinjam":hal_pinjam,"kembalikan":hal_kembalikan,"riwayat_saya":hal_riwayat_saya}
    if (h in admin_only and role!="admin") or (h in peminjam_only and role!="peminjam"):
        hal_dashboard()
    else:
        routes.get(h, hal_dashboard)()

if __name__ == "__main__":
    main()
