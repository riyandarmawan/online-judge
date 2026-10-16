<template>
  <div class="exam-home">
    <panel shadow :padding="24">
      <div slot="title">Ujian</div>
      <p class="lead">
        Algoritma Pemrograman dan Pemrograman Lanjut wajib masuk dengan NIM, nama, dan password/PIN.
        Setelah itu masukkan kode akses sesi. Soal dan pengumpulan hanya terbuka pada waktu yang diatur dosen.
      </p>
      <Alert v-if="!isAuthenticated" type="warning" show-icon>
        Anda belum masuk. Klik tombol di bawah, lalu isi NIM, nama lengkap, dan password/PIN.
        <div style="margin-top: 12px;">
          <Button type="primary" @click="openLogin">Masuk</Button>
        </div>
      </Alert>
      <div v-if="isAuthenticated && (!unlocked.length || isDosen)" class="code-box">
        <Input v-model="accessCode" placeholder="Masukkan kode akses sesi ujian" @on-enter="unlock" style="max-width: 320px"/>
        <Button type="primary" :loading="loading" @click="unlock" style="margin-left: 8px">
          {{ isDosen ? 'Buka sesi' : 'Masuk sesi' }}
        </Button>
      </div>
      
      <Alert v-if="message" :type="messageType" show-icon style="margin-top: 16px">{{ message }}</Alert>
      <div v-if="unlocked.length" class="sessions">
        <Alert v-if="!isDosen" type="success" show-icon style="margin-top: 12px; margin-bottom: 12px">
          Sesi aktif Anda saat ini: <b>{{ unlocked[0].title }}</b> (hanya 1 sesi aktif).
        </Alert>
        <div v-for="session in unlocked" :key="session.id" class="session">
          <strong>{{ session.title }}</strong>
          <span>{{ session.mode === 'archive' ? 'Pemrograman Lanjut (Java/ZIP, tanpa compile)' : 'Algoritma dan Pemrograman (C, dinilai otomatis)' }}</span>
          <Tag :color="session.can_view ? 'green' : 'red'">{{ session.can_view ? 'Soal dibuka' : 'Soal ditutup' }}</Tag>
          <Tag :color="session.can_submit ? 'green' : 'red'">{{ session.can_submit ? 'Submit dibuka' : 'Submit ditutup' }}</Tag>
          <Button v-if="session.can_view" size="small" type="info" @click="$router.push('/problem')">Lihat soal</Button>
        </div>

        <!-- Section untuk ganti sesi bagi mahasiswa -->
        <div v-if="!isDosen" class="switch-box" style="margin-top: 20px; padding-top: 16px; border-top: 1px dashed #dcdee2;">
          <p style="margin-bottom: 8px; color: #515a6e; font-size: 13px;">
            Ingin berpindah ke sesi lain? Masukkan kode akses sesi baru (sesi aktif sebelumnya akan otomatis diganti):
          </p>
          <div class="code-box">
            <Input v-model="accessCode" placeholder="Kode akses sesi baru" @on-enter="unlock" style="max-width: 280px"/>
            <Button type="warning" :loading="loading" @click="unlock" style="margin-left: 8px">Ganti sesi</Button>
          </div>
        </div>
      </div>
    </panel>
  </div>
</template>

<script>
  import { mapGetters, mapActions } from 'vuex'
  import api from '@oj/api'

  export default {
    name: 'home',
    data () {
      return {
        accessCode: '',
        loading: false,
        message: '',
        messageType: 'info',
        unlocked: [],
        isDosen: false
      }
    },
    mounted () {
      this.refresh()
    },
    methods: {
      ...mapActions(['changeModalStatus']),
      openLogin () {
        this.changeModalStatus({visible: true, mode: 'login'})
      },
      refresh () {
        api.getExamStatus().then(res => {
          this.unlocked = res.data.data.unlocked || []
          this.isDosen = !!res.data.data.is_dosen
        })
      },
      unlock () {
        if (!this.isAuthenticated) {
          this.$error('Masuk terlebih dahulu dengan NIM, nama, dan password/PIN')
          this.openLogin()
          return
        }
        if (!this.accessCode.trim()) {
          this.$error('Masukkan kode akses sesi terlebih dahulu')
          return
        }
        this.loading = true
        this.message = ''
        api.unlockExam(this.accessCode.trim()).then(res => {
          this.loading = false
          const data = res.data.data
          this.message = data.message
          this.messageType = data.can_view ? 'success' : 'warning'
          this.accessCode = ''
          this.refresh()
          if (data.can_view) {
            this.$router.push('/problem')
          }
        }, err => {
          this.loading = false
          const msg = (err.data && err.data.data) || 'Gagal mengakses sesi'
          this.message = msg
          this.messageType = 'error'
          if (msg.includes('wajib Masuk')) {
            this.openLogin()
          }
        })
      }
    },
    computed: {
      ...mapGetters(['isAuthenticated'])
    },
    watch: {
      isAuthenticated () {
        this.refresh()
      }
    }
  }
</script>

<style lang="less" scoped>
  .exam-home {
    max-width: 860px;
    width: calc(100% - 32px);
    margin: 24px auto;
    box-sizing: border-box;
  }
  .lead {
    margin-bottom: 16px;
    line-height: 1.6;
  }
  .code-box {
    display: flex;
    align-items: center;
  }
  .session {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-top: 12px;
  }
</style>
