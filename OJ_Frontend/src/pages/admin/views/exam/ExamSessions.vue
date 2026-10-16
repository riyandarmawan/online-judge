<template>
  <div class="view">
    <el-card class="card">
      <div slot="header" class="session-header">
        <span>10 sesi ujian ({{ judgeSessionCount }}/5 Algoritma dan Pemrograman, {{ archiveSessionCount }}/5 Pemrograman Lanjut)</span>
        <el-button type="primary" size="small" @click="showCreateSession">Tambah sesi</el-button>
      </div>
      <p class="hint">
        <b>Algoritma dan Pemrograman</b> menggunakan bahasa C, dikompilasi, dan diberi skor dari jumlah test case yang lulus.
        <b>Pemrograman Lanjut</b> menerima source code Java dalam berkas ZIP tanpa proses compile.
      </p>
      <el-table :data="sessions" v-loading="loading" border>
        <el-table-column prop="slot" label="Sesi" width="70"/>
        <el-table-column label="Nama" min-width="140">
          <template slot-scope="scope">
            <el-input v-model="scope.row.title" size="small"/>
          </template>
        </el-table-column>
        <el-table-column label="Kode akses" width="150">
          <template slot-scope="scope">
            <el-input v-model="scope.row.access_code" size="small"/>
          </template>
        </el-table-column>
        <el-table-column label="Mode" width="170">
          <template slot-scope="scope">
            <el-select v-model="scope.row.mode" size="small">
              <el-option label="Algoritma dan Pemrograman (C)" value="judge"/>
              <el-option label="Pemrograman Lanjut (Java/ZIP)" value="archive"/>
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="Lihat soal" min-width="280">
          <template slot-scope="scope">
            <el-date-picker v-model="scope.row.view_start" type="datetime" value-format="yyyy-MM-ddTHH:mm:ss" placeholder="Buka" size="small"/>
            <el-date-picker v-model="scope.row.view_end" type="datetime" value-format="yyyy-MM-ddTHH:mm:ss" placeholder="Tutup" size="small"/>
            <div class="row-actions">
              <el-tag :type="scope.row.can_view ? 'success' : 'info'" size="mini">{{ scope.row.can_view ? 'Terbuka' : 'Tertutup' }}</el-tag>
              <el-button size="mini" @click="openWindow(scope.row, 'view')">Buka sekarang</el-button>
              <el-button size="mini" @click="closeWindow(scope.row, 'view')">Tutup sekarang</el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="Kumpulkan jawaban" min-width="280">
          <template slot-scope="scope">
            <el-date-picker v-model="scope.row.submit_start" type="datetime" value-format="yyyy-MM-ddTHH:mm:ss" placeholder="Buka" size="small"/>
            <el-date-picker v-model="scope.row.submit_end" type="datetime" value-format="yyyy-MM-ddTHH:mm:ss" placeholder="Tutup" size="small"/>
            <div class="row-actions">
              <el-tag :type="scope.row.can_submit ? 'success' : 'info'" size="mini">{{ scope.row.can_submit ? 'Terbuka' : 'Tertutup' }}</el-tag>
              <el-button size="mini" @click="openWindow(scope.row, 'submit')">Buka sekarang</el-button>
              <el-button size="mini" @click="closeWindow(scope.row, 'submit')">Tutup sekarang</el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="" width="220">
          <template slot-scope="scope">
            <el-button type="primary" size="mini" @click="saveSession(scope.row)">Simpan sesi</el-button>
            <el-button size="mini" @click="loadSubmissions(scope.row)">Lihat jawaban</el-button>
            <div class="row-actions">
              <el-button size="mini" @click="downloadAnswers(scope.row)">Unduh jawaban</el-button>
              <el-button size="mini" @click="downloadScores(scope.row)">Unduh skor</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="card" ref="problemCard">
      <div slot="header" class="problem-card-header">
        <span class="card-title">{{ form.id ? 'Ubah Soal Ujian: ' + form.title : 'Buat Soal Ujian Baru' }}</span>
        <el-tag v-if="selectedSession" :type="selectedSession.mode === 'archive' ? 'warning' : 'success'" size="small">
          {{ selectedSession.slot }}. {{ selectedSession.title }} ({{ selectedSession.mode === 'archive' ? 'Pemrograman Lanjut' : 'Algoritma dan Pemrograman' }})
        </el-tag>
      </div>

      <el-form label-position="top" @submit.native.prevent>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="Sesi Ujian" required>
              <el-select v-model="form.session_id" placeholder="Pilih sesi ujian" style="width: 100%">
                <el-option v-for="session in sessions" :key="session.id" :label="session.slot + '. ' + session.title + (session.mode === 'archive' ? ' [Java/ZIP]' : ' [C]')" :value="session.id"/>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="Display ID (opsional)">
              <el-input v-model="form._id" placeholder="Contoh: A, 1, atau otomatis"/>
            </el-form-item>
          </el-col>
          <el-col :span="10">
            <el-form-item label="Judul Soal" required>
              <el-input v-model="form.title" :placeholder="selectedSession && selectedSession.mode === 'archive' ? 'Contoh: Perpustakaan Digital SmartLib' : 'Masukkan judul soal'"/>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- Banner informasi tipe sesi -->
        <el-alert
          v-if="selectedSession"
          :title="selectedSession.mode === 'archive' ? 'Tipe Soal: Pemrograman Lanjut (Upload PDF Soal & Pengumpulan ZIP Java)' : 'Tipe Soal: Algoritma dan Pemrograman (Bahasa C & Auto-Judge)'"
          :type="selectedSession.mode === 'archive' ? 'success' : 'info'"
          :description="selectedSession.mode === 'archive' ? 'Untuk Pemrograman Lanjut, Anda cukup mengunggah berkas soal berupa PDF. Mahasiswa akan langsung membaca dokumen PDF tersebut di layar dan mengumpulkan arsip ZIP jawaban.' : 'Soal dinilai otomatis menggunakan berkas zip test case I/O standard (stdin/stdout) dengan batas waktu dan memori.'"
          show-icon
          :closable="false"
          style="margin-bottom: 18px">
        </el-alert>

        <!-- KHUSUS PEMROGRAMAN LANJUT: CUKUP UPLOAD PDF SOAL -->
        <template v-if="selectedSession && selectedSession.mode === 'archive'">
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="Unggah Berkas Dokumen Soal (PDF)" required>
                <!-- Jika PDF sudah diunggah -->
                <div v-if="form.pdf_url" class="pdf-uploaded-box" style="display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; background: #f8fbf8; border: 1px solid #b7eb8f; border-radius: 6px; margin-bottom: 8px;">
                  <div style="display: flex; align-items: center; gap: 14px;">
                    <i class="el-icon-document" style="font-size: 32px; color: #f5222d;"></i>
                    <div>
                      <strong style="font-size: 15px; color: #262626;">{{ form.pdf_name || 'Dokumen_Soal.pdf' }}</strong>
                      <div style="font-size: 12px; color: #52c41a; margin-top: 2px;">
                        <i class="el-icon-circle-check"></i> Berkas PDF siap ditampilkan ke mahasiswa
                      </div>
                    </div>
                  </div>
                  <div>
                    <el-button size="small" type="primary" icon="el-icon-view" @click="openPdf(form.pdf_url)">Lihat PDF</el-button>
                    <el-button size="small" type="danger" icon="el-icon-delete" @click="removePdf">Ganti Berkas</el-button>
                  </div>
                </div>

                <!-- Komponen Drag & Drop Upload PDF -->
                <el-upload
                  v-else
                  class="pdf-uploader"
                  drag
                  action="/api/admin/upload_file"
                  name="file"
                  accept=".pdf,application/pdf"
                  :show-file-list="false"
                  :on-success="uploadPdfSuccess"
                  :on-error="uploadPdfFailed"
                  style="width: 100%;">
                  <i class="el-icon-upload" style="font-size: 48px; color: #409eff; margin: 16px 0 10px;"></i>
                  <div class="el-upload__text" style="font-size: 14px;">
                    Tarik berkas PDF soal ke sini atau <em>klik untuk memilih berkas</em>
                  </div>
                  <div class="el-upload__tip" slot="tip" style="color: #8c8c8c; margin-top: 6px;">
                    Hanya menerima berkas berformat <b>.pdf</b>. Berkas akan otomatis ditampilkan dalam PDF viewer di halaman ujian mahasiswa.
                  </div>
                </el-upload>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="Format Nama Berkas Jawaban Mahasiswa (.zip)" required>
                <el-input v-model="form.answer_filename" placeholder="contoh: {NIM}_{NAMA}_soal.zip atau nim_nama_soal.zip"/>
                <div class="hint" style="margin-top: 4px; color: #808695; font-size: 12px;">
                  Gunakan <code>{NIM}</code> dan <code>{NAMA}</code> agar nama berkas otomatis menyesuaikan (contoh: <code>{NIM}_{NAMA}_perpustakaan.zip</code> atau <code>nim_nama_perpustakaan.zip</code>). Gunakan <code>*.zip</code> jika nama berkas bebas.
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="Catatan / Petunjuk Tambahan Mahasiswa (opsional)">
                <el-input type="textarea" :rows="2" v-model="form.hint" placeholder="Catatan singkat jika ada (opsional)..."/>
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <!-- KHUSUS ALGORITMA DAN PEMROGRAMAN (JUDGE MODE: C) -->
        <template v-else-if="selectedSession && selectedSession.mode === 'judge'">
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="Deskripsi Soal" required>
                <Simditor v-model="form.description"/>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="Format Input" required>
                <Simditor v-model="form.input_description"/>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="Format Output" required>
                <Simditor v-model="form.output_description"/>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- Samples -->
          <div class="samples-section">
            <div class="section-title">Contoh Kasus (Samples)</div>
            <div v-for="(sample, index) in form.samples" :key="'sample' + index" class="sample-item">
              <Accordion :title="'Contoh ' + (index + 1)">
                <el-button type="warning" size="mini" icon="el-icon-delete" slot="header" @click="deleteSample(index)">
                  Hapus Contoh
                </el-button>
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="Input Contoh" required>
                      <el-input type="textarea" :rows="4" v-model="sample.input" placeholder="Masukkan input contoh"/>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="Output Contoh" required>
                      <el-input type="textarea" :rows="4" v-model="sample.output" placeholder="Masukkan output contoh"/>
                    </el-form-item>
                  </el-col>
                </el-row>
              </Accordion>
            </div>
            <div class="add-sample-btn">
              <button type="button" class="add-samples" @click="addSample()">
                <i class="el-icon-plus"></i> Tambah Contoh Kasus
              </button>
            </div>
          </div>

          <el-form-item label="Petunjuk / Hint (opsional)">
            <Simditor v-model="form.hint"/>
          </el-form-item>

          <div class="section-title">Ketentuan Algoritma dan Pemrograman (Bahasa C & Auto-Judge)</div>
          <el-row :gutter="20">
            <el-col :span="6">
              <el-form-item label="Batas Waktu (ms)" required>
                <el-input-number v-model="form.time_limit" :min="1" :max="60000" style="width: 100%"/>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="Batas Memori (MB)" required>
                <el-input-number v-model="form.memory_limit" :min="1" :max="1024" style="width: 100%"/>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="Berkas Zip Test Case" required>
                <el-upload
                  action="/api/admin/test_case"
                  name="file"
                  :data="{spj: false}"
                  :show-file-list="true"
                  :on-success="uploadTestCaseSuccess"
                  :on-error="uploadTestCaseFailed">
                  <el-button size="small" type="primary" icon="el-icon-upload">Unggah Berkas ZIP</el-button>
                </el-upload>
                <div class="hint">Zip berisi pasangan 1.in, 1.out, 2.in, 2.out, dst. {{ form.test_case_count ? form.test_case_count + ' test case tersimpan.' : '' }}</div>
              </el-form-item>
            </el-col>
          </el-row>

          <div v-if="form.test_case_score && form.test_case_score.length" style="margin-bottom: 16px">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px">
              <span style="font-weight: 600; font-size: 13px">Daftar Test Case & Bobot Skor (Total Skor: {{ currentTotalScore }})</span>
              <el-button size="mini" @click="distributeScoresEvenly">Bagi Rata (Total 100)</el-button>
            </div>
            <el-table :data="form.test_case_score" border size="mini" max-height="250">
              <el-table-column prop="input_name" label="Input"/>
              <el-table-column prop="output_name" label="Output"/>
              <el-table-column label="Skor" width="140">
                <template slot-scope="scope">
                  <el-input-number size="mini" v-model="scope.row.score" :min="0" :max="100"/>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>

        <el-form-item style="margin-top: 24px">
          <el-button type="primary" :loading="saving" @click="saveProblem">
            {{ form.id ? 'Perbarui Soal' : 'Simpan Soal' }}
          </el-button>
          <el-button @click="resetForm">Batal</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="problems" border style="margin-top: 20px">
        <el-table-column prop="_id" label="ID" width="120"/>
        <el-table-column prop="title" label="Judul"/>
        <el-table-column label="Sesi" width="80">
          <template slot-scope="scope">{{ sessionSlot(scope.row.session_id) }}</template>
        </el-table-column>
        <el-table-column label="Ketentuan" min-width="180">
          <template slot-scope="scope">
            <span v-if="scope.row.mode === 'archive'">{{ scope.row.answer_filename }}</span>
            <span v-else>{{ scope.row.test_case_count }} test case, bahasa C (Algoritma dan Pemrograman)</span>
          </template>
        </el-table-column>
        <el-table-column label="" width="160">
          <template slot-scope="scope">
            <el-button size="mini" @click="editProblem(scope.row)">Ubah</el-button>
            <el-button size="mini" type="danger" @click="removeProblem(scope.row)">Hapus</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="card" v-if="activeSession">
      <div slot="header">Jawaban {{ activeSession.title }}</div>
      <template v-if="activeSession.mode === 'judge'">
        <h4>Skor terbaik per mahasiswa</h4>
        <el-table :data="bundle.scores" border>
          <el-table-column prop="username" label="Mahasiswa"/>
          <el-table-column prop="problem_title" label="Soal"/>
          <el-table-column prop="passed" label="Lulus" width="80"/>
          <el-table-column prop="total" label="Total" width="80"/>
          <el-table-column prop="score" label="Skor" width="80"/>
          <el-table-column prop="create_time" label="Waktu"/>
        </el-table>
        <h4>Semua pengiriman</h4>
        <el-table :data="bundle.code_submissions" border>
          <el-table-column prop="username" label="Mahasiswa" width="140"/>
          <el-table-column prop="problem_title" label="Soal"/>
          <el-table-column prop="score" label="Skor" width="80"/>
          <el-table-column label="Test case" width="100">
            <template slot-scope="scope">{{ scope.row.passed }}/{{ scope.row.total }}</template>
          </el-table-column>
          <el-table-column prop="create_time" label="Waktu" width="220"/>
          <el-table-column label="" width="100">
            <template slot-scope="scope">
              <el-button size="mini" @click="codeDialog = scope.row">Lihat kode</el-button>
            </template>
          </el-table-column>
        </el-table>
      </template>
      <el-table v-else :data="bundle.zip_submissions" border>
        <el-table-column prop="username" label="NIM Mahasiswa" width="140">
          <template slot-scope="scope">
            <strong>{{ scope.row.username }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="real_name" label="Nama Mahasiswa" min-width="150"/>
        <el-table-column prop="problem_title" label="Soal" min-width="150"/>
        <el-table-column prop="original_name" label="Nama Berkas ZIP" min-width="180"/>
        <el-table-column prop="create_time" label="Waktu Kumpul" width="180"/>
        <el-table-column label="" width="110">
          <template slot-scope="scope">
            <el-button size="mini" type="primary" icon="el-icon-download" @click="downloadZip(scope.row)">Unduh</el-button>
          </template>
        </el-table-column>
      </el-table>
      <h4 style="margin-top: 18px; margin-bottom: 8px;">Mahasiswa terdaftar di sesi ini ({{ (bundle.students || []).length }})</h4>
      <el-table :data="bundle.students" border style="margin-bottom: 16px">
        <el-table-column prop="username" label="NIM Mahasiswa" width="140">
          <template slot-scope="scope">
            <strong>{{ scope.row.username }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="real_name" label="Nama Lengkap" min-width="160"/>
        <el-table-column prop="create_time" label="Waktu Terdaftar" width="200"/>
        <el-table-column label="Aksi" width="280">
          <template slot-scope="scope">
            <el-button size="mini" type="warning" icon="el-icon-key" @click="resetPassword(scope.row)">Reset Password</el-button>
            <el-button size="mini" type="danger" icon="el-icon-refresh-right" @click="resetStudent(scope.row)">Reset Sesi</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog title="Kode jawaban" :visible.sync="codeVisible" width="70%">
      <pre class="code">{{ codeDialog && codeDialog.code }}</pre>
    </el-dialog>

    <el-dialog title="Tambah sesi ujian" :visible.sync="createSessionVisible" width="460px">
      <el-form label-width="120px" @submit.native.prevent>
        <el-form-item label="Nama sesi">
          <el-input v-model="newSession.title" placeholder="Contoh: Ujian Pemrograman 1"/>
        </el-form-item>
        <el-form-item label="Kode akses">
          <el-input v-model="newSession.access_code" placeholder="Kode yang diberikan ke mahasiswa"/>
        </el-form-item>
        <el-form-item label="Mode">
          <el-select v-model="newSession.mode" style="width: 100%">
            <el-option label="Algoritma dan Pemrograman (C)" value="judge"/>
            <el-option label="Pemrograman Lanjut (Java/ZIP)" value="archive"/>
          </el-select>
        </el-form-item>
      </el-form>
      <span slot="footer">
        <el-button @click="createSessionVisible = false">Batal</el-button>
        <el-button type="primary" :loading="creatingSession" @click="createSession">Tambah sesi</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
  import Simditor from '../../components/Simditor'
  import Accordion from '../../components/Accordion'
  import api from '../../api'

  function emptyForm () {
    return {
      id: null,
      _id: '',
      session_id: null,
      title: '',
      description: '',
      input_description: '',
      output_description: '',
      samples: [],
      hint: '',
      answer_filename: '{NIM}_Jawaban.zip',
      time_limit: 1000,
      memory_limit: 256,
      test_case_id: '',
      test_case_count: 0,
      test_case_score: [],
      pdf_url: '',
      pdf_name: ''
    }
  }

  export default {
    name: 'ExamSessions',
    components: {
      Simditor,
      Accordion
    },
    data () {
      return {
        loading: false,
        saving: false,
        sessions: [],
        problems: [],
        form: emptyForm(),
        activeSession: null,
        bundle: {scores: [], code_submissions: [], zip_submissions: []},
        codeDialog: null,
        createSessionVisible: false,
        creatingSession: false,
        newSession: {
          title: '',
          access_code: '',
          mode: 'judge'
        }
      }
    },
    computed: {
      judgeSessionCount () {
        return this.sessions.filter(item => item.mode === 'judge').length
      },
      archiveSessionCount () {
        return this.sessions.filter(item => item.mode === 'archive').length
      },
      selectedSession () {
        return this.sessions.find(item => item.id === this.form.session_id) || null
      },
      currentTotalScore () {
        if (!this.form.test_case_score || !this.form.test_case_score.length) return 0
        return this.form.test_case_score.reduce((sum, item) => sum + (parseInt(item.score, 10) || 0), 0)
      },
      codeVisible: {
        get () {
          return !!this.codeDialog
        },
        set (value) {
          if (!value) this.codeDialog = null
        }
      }
    },
    mounted () {
      this.load()
    },
    methods: {
      toPicker (iso) {
        if (!iso) return null
        const date = new Date(iso)
        if (isNaN(date.getTime())) return null
        const pad = value => String(value).padStart(2, '0')
        return date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(date.getDate()) + 'T' + pad(date.getHours()) + ':' + pad(date.getMinutes()) + ':' + pad(date.getSeconds())
      },
      toIso (value) {
        if (!value) return null
        const date = new Date(value)
        if (isNaN(date.getTime())) return null
        return date.toISOString()
      },
      load () {
        this.loading = true
        api.getExamDesk().then(res => {
          this.loading = false
          const data = res.data.data
          this.sessions = (data.sessions || []).map(session => {
            ;['view_start', 'view_end', 'submit_start', 'submit_end'].forEach(key => {
              session[key] = this.toPicker(session[key])
            })
            return session
          })
          this.problems = data.problems || []
        }, () => {
          this.loading = false
        })
      },
      sessionPayload (row) {
        return {
          id: row.id,
          title: row.title,
          access_code: row.access_code,
          mode: row.mode,
          view_start: this.toIso(row.view_start),
          view_end: this.toIso(row.view_end),
          submit_start: this.toIso(row.submit_start),
          submit_end: this.toIso(row.submit_end)
        }
      },
      saveSession (row) {
        api.saveExamSession(this.sessionPayload(row)).then(() => this.load())
      },
      showCreateSession () {
        if (this.sessions.length >= 10) {
          this.$error('Maksimal 10 sesi ujian sudah tercapai')
          return
        }
        this.newSession = {title: '', access_code: '', mode: 'judge'}
        this.createSessionVisible = true
      },
      createSession () {
        if (!this.newSession.title.trim() || !this.newSession.access_code.trim()) {
          this.$error('Nama sesi dan kode akses wajib diisi')
          return
        }
        this.creatingSession = true
        api.createExamSession(this.newSession).then(() => {
          this.creatingSession = false
          this.createSessionVisible = false
          this.load()
        }, () => {
          this.creatingSession = false
        })
      },
      openWindow (row, kind) {
        const start = new Date()
        const currentEnd = row[kind + '_end'] ? new Date(row[kind + '_end']) : null
        const end = currentEnd && currentEnd > start ? currentEnd : new Date(start.getTime() + 2 * 60 * 60 * 1000)
        row[kind + '_start'] = this.toPicker(start.toISOString())
        row[kind + '_end'] = this.toPicker(end.toISOString())
        this.saveSession(row)
      },
      closeWindow (row, kind) {
        const end = new Date(Date.now() - 1000)
        if (!row[kind + '_start']) {
          row[kind + '_start'] = this.toPicker(new Date(end.getTime() - 60000).toISOString())
        }
        row[kind + '_end'] = this.toPicker(end.toISOString())
        this.saveSession(row)
      },
      sessionSlot (id) {
        const session = this.sessions.find(item => item.id === id)
        return session ? session.slot : '-'
      },
      addSample () {
        this.form.samples.push({input: '', output: ''})
      },
      deleteSample (index) {
        this.form.samples.splice(index, 1)
      },
      uploadTestCaseSuccess (response) {
        if (response.error) {
          this.$error(response.data)
          return
        }
        const data = response.data
        const fileList = data.info || []
        const count = fileList.length
        const share = count ? Math.floor(100 / count) : 0
        const rem = count ? 100 - share * count : 0
        for (let i = 0; i < count; i++) {
          fileList[i].score = i === 0 ? share + rem : share
        }
        this.form.test_case_score = fileList
        this.form.test_case_count = count
        this.form.test_case_id = data.id || data.test_case_id
        this.$success(`Berhasil mengunggah ${count} test case`)
      },
      uploadTestCaseFailed () {
        this.$error('Gagal mengunggah berkas zip test case')
      },
      distributeScoresEvenly () {
        const list = this.form.test_case_score
        if (!list || !list.length) return
        const count = list.length
        const share = Math.floor(100 / count)
        const rem = 100 - share * count
        list.forEach((item, idx) => {
          item.score = idx === 0 ? share + rem : share
        })
      },
      resetForm () {
        this.form = emptyForm()
      },
      editProblem (row) {
        this.form = {
          id: row.id,
          _id: row._id || '',
          session_id: row.session_id,
          title: row.title || '',
          description: row.description || row.description_text || '',
          input_description: row.input_description || '',
          output_description: row.output_description || '',
          samples: (row.samples && row.samples.length) ? JSON.parse(JSON.stringify(row.samples)) : [],
          hint: row.hint || '',
          answer_filename: row.answer_filename || '',
          time_limit: row.time_limit || 1000,
          memory_limit: row.memory_limit || 256,
          test_case_id: row.test_case_id || '',
          test_case_count: row.test_case_count || 0,
          test_case_score: (row.test_case_score && row.test_case_score.length) ? JSON.parse(JSON.stringify(row.test_case_score)) : [],
          pdf_url: row.pdf_url || '',
          pdf_name: row.pdf_name || ''
        }
        const el = this.$refs.problemCard
        if (el && el.$el) {
          el.$el.scrollIntoView({behavior: 'smooth'})
        }
      },
      uploadPdfSuccess (response) {
        if (response.success && response.file_path) {
          this.form.pdf_url = response.file_path
          this.form.pdf_name = response.file_name || 'Dokumen_Soal.pdf'
          if (!this.form.title) {
            const base = (response.file_name || '').replace(/\.[^/.]+$/, '').replace(/[_\\-]/g, ' ')
            this.form.title = base
          }
          this.$success('Berkas PDF soal berhasil diunggah')
        } else {
          this.$error(response.msg || 'Gagal mengunggah PDF')
        }
      },
      uploadPdfFailed () {
        this.$error('Gagal mengunggah berkas PDF soal')
      },
      removePdf () {
        this.form.pdf_url = ''
        this.form.pdf_name = ''
      },
      openPdf (url) {
        if (url) {
          window.open(url, '_blank')
        }
      },
      saveProblem () {
        const session = this.selectedSession
        if (!session) {
          this.$error('Pilih sesi ujian terlebih dahulu')
          return
        }
        if (!this.form.title.trim()) {
          this.$error('Judul soal wajib diisi')
          return
        }
        if (session.mode === 'judge') {
          if (!this.form.description.trim()) {
            this.$error('Deskripsi soal wajib diisi')
            return
          }
          if (!this.form.test_case_id) {
            this.$error('Soal Algoritma dan Pemrograman membutuhkan test case. Silakan unggah berkas zip test case.')
            return
          }
        }
        if (session.mode === 'archive') {
          if (!this.form.pdf_url && this.form.description) {
            const linkMatch = this.form.description.match(/href=["']([^"']+\.pdf)["']/i) ||
                              this.form.description.match(/(\/public\/upload\/[a-zA-Z0-9_\-]+\.pdf)/i)
            if (linkMatch) {
              this.form.pdf_url = linkMatch[1]
              const nameMatch = this.form.description.match(/>([^<]+\.pdf)<\/a>/i)
              if (nameMatch) {
                this.form.pdf_name = nameMatch[1]
              }
            } else if (this.form.description.includes('uts_perpustakaan')) {
              this.form.pdf_url = '/public/upload/85441fca5e.pdf'
              this.form.pdf_name = 'uts_perpustakaan-digital-kampus.pdf'
            }
          }

          if (this.form.answer_filename) {
            this.form.answer_filename = this.form.answer_filename.replace(/<[^>]*>/g, '').trim()
          }

          if (this.form.hint) {
            this.form.hint = this.form.hint.replace(/<[^>]*>/g, '').trim()
          }

          if (!this.form.pdf_url) {
            this.$error('Silakan unggah berkas PDF soal terlebih dahulu')
            return
          }
          if (!this.form.answer_filename.trim()) {
            this.$error('Format nama berkas zip jawaban wajib diisi untuk Pemrograman Lanjut')
            return
          }
        }

        this.saving = true
        const payload = {
          id: this.form.id,
          _id: this.form._id,
          session_id: this.form.session_id,
          title: this.form.title,
          description: this.form.description,
          input_description: this.form.input_description,
          output_description: session.mode === 'archive' ? '<p>-</p>' : this.form.output_description,
          samples: session.mode === 'archive' ? [] : this.form.samples,
          hint: this.form.hint,
          answer_filename: this.form.answer_filename,
          time_limit: session.mode === 'archive' ? 1000 : this.form.time_limit,
          memory_limit: session.mode === 'archive' ? 256 : this.form.memory_limit,
          test_case_id: session.mode === 'archive' ? 'none' : this.form.test_case_id,
          test_case_score: session.mode === 'archive' ? [] : this.form.test_case_score,
          pdf_url: this.form.pdf_url,
          pdf_name: this.form.pdf_name
        }
        const request = this.form.id ? api.updateExamProblem(payload) : api.saveExamProblem(payload)
        request.then(() => {
          this.saving = false
          this.$success(this.form.id ? 'Soal berhasil diperbarui' : 'Soal berhasil disimpan')
          this.resetForm()
          this.load()
        }, () => {
          this.saving = false
        })
      },
      removeProblem (row) {
        this.$confirm('Hapus soal ini dari ujian?', 'Konfirmasi', {type: 'warning'}).then(() => {
          api.deleteExamProblem(row.id).then(() => this.load())
        }).catch(() => {})
      },
      loadSubmissions (row) {
        this.activeSession = row
        api.getExamSubmissions(row.id).then(res => {
          this.bundle = res.data.data
        })
      },
      downloadAnswers (row) {
        window.open('/api/admin/exam/download/answers?session_id=' + row.id)
      },
      downloadScores (row) {
        window.open('/api/admin/exam/download/scores?session_id=' + row.id)
      },
      downloadZip (row) {
        window.open('/api/admin/exam/answer_file?id=' + row.id)
      },
      resetStudent (row) {
        this.$confirm(`Reset sesi untuk mahasiswa ${row.username}? Mahasiswa akan dapat memasukkan kode sesi lain.`, 'Konfirmasi', {type: 'warning'}).then(() => {
          api.resetExamStudentSession(row.user_id).then(() => {
            this.$success('Sesi mahasiswa berhasil direset')
            this.loadSubmissions(this.activeSession)
          })
        }).catch(() => {})
      },
      resetPassword (row) {
        this.$confirm(`Reset Password / PIN untuk mahasiswa ${row.username} (${row.real_name || ''})? Mahasiswa dapat membuat Password/PIN baru saat login berikutnya.`, 'Konfirmasi Reset Password', {type: 'warning'}).then(() => {
          api.resetStudentPassword(row.user_id).then(() => {
            this.$success('Password mahasiswa berhasil direset')
          })
        }).catch(() => {})
      }
    }
  }
</script>

<style scoped>
  .card {
    margin-bottom: 16px;
  }
  .session-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .problem-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .card-title {
    font-weight: 600;
    font-size: 15px;
  }
  .section-title {
    font-size: 14px;
    font-weight: 600;
    color: #333;
    margin: 18px 0 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid #ebeef5;
  }
  .samples-section {
    margin-bottom: 16px;
  }
  .sample-item {
    margin-bottom: 12px;
  }
  .add-samples {
    width: 100%;
    background-color: #fff;
    border: 1px dashed #dcdfe6;
    border-radius: 4px;
    outline: none;
    cursor: pointer;
    color: #606266;
    height: 36px;
    font-size: 13px;
    transition: all 0.2s;
  }
  .add-samples:hover {
    background-color: #f5f7fa;
    border-color: #409EFF;
    color: #409EFF;
  }
  .add-samples i {
    margin-right: 6px;
  }
  .add-sample-btn {
    margin-top: 8px;
    margin-bottom: 16px;
  }
  .hint {
    color: #666;
    font-size: 13px;
    margin: 6px 0 12px;
  }
  .row-actions {
    margin-top: 6px;
  }
  .code {
    white-space: pre-wrap;
    max-height: 480px;
    overflow: auto;
  }
  .pdf-uploader /deep/ .el-upload {
    width: 100%;
  }
  .pdf-uploader /deep/ .el-upload-dragger {
    width: 100%;
    height: 160px;
  }
</style>
