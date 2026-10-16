<template>
  <div class="flex-container">
    <div id="problem-main">
      <!--problem main-->
      <Panel :padding="40" shadow>
        <div slot="title">{{problem.title}}</div>
        <div id="problem-content" class="markdown-body" v-katex>
          <!-- Khusus Pemrograman Lanjut (archive mode: Soal Berupa Dokumen PDF) -->
          <template v-if="problem.exam_mode === 'archive'">
            <div class="pdf-exam-header" style="display: flex; justify-content: space-between; align-items: center; background: #f8fbfd; border: 1px solid #d9e9f7; border-radius: 6px; padding: 14px 20px; margin-bottom: 18px;">
              <div style="display: flex; align-items: center; gap: 14px;">
                <Icon type="document-text" style="font-size: 32px; color: #ed3f14;"></Icon>
                <div>
                  <strong style="font-size: 15px; color: #17233d;">Dokumen Soal Ujian (PDF)</strong>
                  <div style="font-size: 12px; color: #515a6e; margin-top: 2px;">{{ problem.pdf_name || (problem.title + '.pdf') }}</div>
                </div>
              </div>
              <div>
                <Button type="primary" icon="arrow-down-a" @click="downloadPdf">Unduh PDF Soal</Button>
                <Button type="ghost" icon="android-open" @click="openPdfNewTab" style="margin-left: 8px">Buka di Tab Baru</Button>
              </div>
            </div>

            <!-- PDF Viewer Iframe -->
            <div v-if="pdfSource" class="pdf-viewer-wrap" style="margin-bottom: 20px;">
              <iframe :src="pdfSource" width="100%" height="860px" style="border: 1px solid #dcdee2; border-radius: 6px; box-shadow: 0 1px 4px rgba(0,0,0,0.08);"></iframe>
            </div>
            <div v-else-if="problem.description" class="content" v-html="problem.description" style="margin-bottom: 20px;"></div>

            <div v-if="problem.hint" style="margin-top: 16px;">
              <p class="title">Petunjuk / Catatan Tambahan</p>
              <Card dis-hover>
                <div class="content" v-html="problem.hint"></div>
              </Card>
            </div>
          </template>

          <!-- Mode biasa / Algoritma dan Pemrograman (judge mode: C & Test Cases) -->
          <template v-else>
            <p class="title">{{$t('m.Description')}}</p>
            <p class="content" v-html=problem.description></p>

            <p class="title">{{$t('m.Input')}} <span v-if="problem.io_mode.io_mode=='File IO'">({{$t('m.FromFile')}}: {{ problem.io_mode.input }})</span></p>
            <p class="content" v-html=problem.input_description></p>

            <p class="title">{{$t('m.Output')}} <span v-if="problem.io_mode.io_mode=='File IO'">({{$t('m.ToFile')}}: {{ problem.io_mode.output }})</span></p>
            <p class="content" v-html=problem.output_description></p>

            <div v-for="(sample, index) of problem.samples" :key="index" v-if="sample.input || sample.output">
              <div class="flex-container sample">
                <div class="sample-input">
                  <p class="title">{{$t('m.Sample_Input')}} {{index + 1}}
                    <a class="copy"
                       v-clipboard:copy="sample.input"
                       v-clipboard:success="onCopy"
                       v-clipboard:error="onCopyError">
                      <Icon type="clipboard"></Icon>
                    </a>
                  </p>
                  <pre>{{sample.input}}</pre>
                </div>
                <div class="sample-output">
                  <p class="title">{{$t('m.Sample_Output')}} {{index + 1}}</p>
                  <pre>{{sample.output}}</pre>
                </div>
              </div>
            </div>

            <div v-if="problem.hint">
              <p class="title">{{$t('m.Hint')}}</p>
              <Card dis-hover>
                <div class="content" v-html=problem.hint></div>
              </Card>
            </div>
          </template>

          <div v-if="problem.source">
            <p class="title">{{$t('m.Source')}}</p>
            <p class="content">{{problem.source}}</p>
          </div>

        </div>
      </Panel>
      <!--problem main end-->
      <Card :padding="20" id="submit-code" dis-hover>
        <Alert v-if="problem.exam_mode && problem.can_submit === false" type="warning" show-icon>
          Akses pengumpulan jawaban sedang ditutup.
        </Alert>
        <template v-if="problem.exam_mode === 'archive'">
          <div class="archive-submission-card" style="padding: 10px 0;">
            <div style="margin-bottom: 16px;">
              <h3 style="font-size: 16px; font-weight: 600; color: #17233d; margin-bottom: 4px;">
                
                Pengumpulan Berkas Jawaban (Pemrograman Lanjut)
              </h3>
              <p style="color: #808695; font-size: 13px;">
                Unggah berkas arsip <b>.zip</b> berisi project / source code Java Anda. Mahasiswa <b>tidak perlu login</b>.
              </p>
            </div>

            <!-- Ketentuan Nama Berkas Dari Dosen -->
            <Alert style="margin-bottom: 16px;">
              Ketentuan Format Nama Berkas: 
              <b style="color: #ed3f14; font-size: 14px;">{{ problem.answer_filename_template || problem.answer_filename || '{NIM}_{NAMA}_soal.zip' }}</b>
              <div style="font-size: 12px; color: #515a6e; margin-top: 4px;">
                Contoh nama berkas Anda: <code>{{ sampleExpectedFilename }}</code>
              </div>
            </Alert>

            <!-- Status Terakhir Dikumpulkan -->
            <Alert v-if="myZip" type="success" show-icon style="margin-bottom: 16px;">
              <b>Jawaban Berhasil Tersimpan:</b> {{ myZip.original_name }}
              <span v-if="myZip.create_time" style="color: #808695; font-size: 12px; margin-left: 6px;">
                (Waktu: {{ formatTime(myZip.create_time) }})
              </span>
              <div v-if="myZip.student_info" style="font-size: 12px; margin-top: 2px;">
                Identitas: <b>{{ myZip.student_info }}</b>
              </div>
              <div style="font-size: 12px; color: #19be6b; margin-top: 4px;">
                <Icon type="checkmark-circled"></Icon> Anda dapat mengunggah berkas baru untuk memperbarui jawaban sebelum waktu ujian berakhir.
              </div>
            </Alert>

            <Form label-position="top">
              <Row :gutter="16">
                <Col :span="12">
                  <FormItem label="NIM Mahasiswa" required>
                    <Input v-model="zipForm.nim" placeholder="Contoh: 2508394" size="large">
                      <Icon type="ios-person-outline" slot="prepend"></Icon>
                    </Input>
                  </FormItem>
                </Col>
                <Col :span="12">
                  <FormItem label="Nama Lengkap Mahasiswa" required>
                    <Input v-model="zipForm.name" placeholder="Contoh: Budi Santoso" size="large">
                      <Icon type="ios-contact-outline" slot="prepend"></Icon>
                    </Input>
                  </FormItem>
                </Col>
              </Row>

              <FormItem label="Pilih Berkas Jawaban (.zip)" required>
                <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap; padding: 12px; background: #fafafa; border: 1px dashed #dcdee2; border-radius: 6px;">
                  <label>
                    <input type="file" accept=".zip,application/zip" @change="onZipSelected" style="display: none;"/>
                    <Button type="ghost" icon="ios-cloud-upload-outline" size="default" @click="$el.querySelector('input[type=file]').click()">
                      {{ zipFile ? 'Ganti Berkas ZIP' : 'Pilih Berkas ZIP' }}
                    </Button>
                  </label>
                  <span v-if="zipFile" style="font-size: 14px; font-weight: 500; color: #2d8cf0;">
                    <Icon type="document"></Icon> {{ zipFile.name }} ({{ formatFileSize(zipFile.size) }})
                  </span>
                  <span v-else style="font-size: 13px; color: #808695;">
                    Belum ada berkas ZIP yang dipilih
                  </span>
                </div>
              </FormItem>

              <div style="margin-top: 14px; display: flex; justify-content: flex-end;">
                <Button type="primary" size="large" icon="upload" :loading="submitting" @click="submitZip"
                        :disabled="problem.can_submit === false">
                  Kumpulkan Jawaban
                </Button>
              </div>
            </Form>
          </div>
        </template>
        <template v-else>
        <CodeMirror :value.sync="code"
                    :languages="problem.languages"
                    :language="language"
                    :theme="theme"
                    @resetCode="onResetToTemplate"
                    @changeTheme="onChangeTheme"
                    @changeLang="onChangeLang"></CodeMirror>
        <Row type="flex" justify="space-between">
          <Col :span="10">
            <div class="status" v-if="statusVisible">
              <template v-if="!this.contestID || (this.contestID && OIContestRealTimePermission)">
                <span>{{$t('m.Status')}}</span>
                <Tag type="dot" :color="submissionStatus.color" @click.native="handleRoute('/status/'+submissionId)">
                  {{$t('m.' + submissionStatus.text.replace(/ /g, "_"))}}
                </Tag>
                <div v-if="result.statistic_info && result.statistic_info.total">
                  Skor {{ result.statistic_info.score }} ({{ result.statistic_info.passed }}/{{ result.statistic_info.total }} test case lulus)
                </div>
              </template>
              <template v-else-if="this.contestID && !OIContestRealTimePermission">
                <Alert type="success" show-icon>{{$t('m.Submitted_successfully')}}</Alert>
              </template>
            </div>
            <div v-else-if="problem.my_status === 0">
              <Alert type="success" show-icon>{{$t('m.You_have_solved_the_problem')}}</Alert>
            </div>
            <div v-else-if="this.contestID && !OIContestRealTimePermission && submissionExists">
              <Alert type="success" show-icon>{{$t('m.You_have_submitted_a_solution')}}</Alert>
            </div>
            <div v-if="contestEnded">
              <Alert type="warning" show-icon>{{$t('m.Contest_has_ended')}}</Alert>
            </div>
          </Col>

          <Col :span="12">
            <template v-if="captchaRequired">
              <div class="captcha-container">
                <Tooltip v-if="captchaRequired" content="Click to refresh" placement="top">
                  <img :src="captchaSrc" @click="getCaptchaSrc"/>
                </Tooltip>
                <Input v-model="captchaCode" class="captcha-code"/>
              </div>
            </template>
            <Button type="warning" icon="edit" :loading="submitting" @click="submitCode"
                    :disabled="problemSubmitDisabled || submitted || problem.can_submit === false"
                    class="fl-right">
              <span v-if="submitting">{{$t('m.Submitting')}}</span>
              <span v-else>{{$t('m.Submit')}}</span>
            </Button>
          </Col>
        </Row>
        </template>
      </Card>
    </div>

    <div id="right-column">
      <VerticalMenu @on-click="handleRoute">
        <template v-if="this.contestID">
          <VerticalMenu-item :route="{name: 'contest-problem-list', params: {contestID: contestID}}">
            <Icon type="ios-photos"></Icon>
            {{$t('m.Problems')}}
          </VerticalMenu-item>

          <VerticalMenu-item :route="{name: 'contest-announcement-list', params: {contestID: contestID}}">
            <Icon type="chatbubble-working"></Icon>
            {{$t('m.Announcements')}}
          </VerticalMenu-item>
        </template>

        <VerticalMenu-item v-if="!this.contestID || OIContestRealTimePermission" :route="submissionRoute">
          <Icon type="navicon-round"></Icon>
           {{$t('m.Submissions')}}
        </VerticalMenu-item>

        <template v-if="this.contestID">
          <VerticalMenu-item v-if="!this.contestID || OIContestRealTimePermission"
                             :route="{name: 'contest-rank', params: {contestID: contestID}}">
            <Icon type="stats-bars"></Icon>
            {{$t('m.Rankings')}}
          </VerticalMenu-item>
          <VerticalMenu-item :route="{name: 'contest-details', params: {contestID: contestID}}">
            <Icon type="home"></Icon>
            {{$t('m.View_Contest')}}
          </VerticalMenu-item>
        </template>
      </VerticalMenu>

      <Card id="info">
        <div slot="title" class="header">
          <Icon type="information-circled"></Icon>
          <span class="card-title">{{$t('m.Information')}}</span>
        </div>
        <ul>
          <li><p>ID</p>
            <p>{{problem._id}}</p></li>
          <template v-if="problem.exam_mode === 'archive'">
            <li>
              <p>Mata Kuliah</p>
              <p>Pemrograman Lanjut</p>
            </li>
          </template>
          <template v-else>
            <li v-if="problem.exam_mode === 'judge'">
              <p>Mata Kuliah</p>
              <p>Algoritma dan Pemrograman</p>
            </li>
            <li>
              <p>{{$t('m.Time_Limit')}}</p>
              <p>{{problem.time_limit}}MS</p></li>
            <li>
              <p>{{$t('m.Memory_Limit')}}</p>
              <p>{{problem.memory_limit}}MB</p></li>
            <li>
              <p>{{$t('m.IOMode')}}</p>
              <p>{{problem.io_mode.io_mode}}</p>
            </li>
          </template>

          <li v-if="problem.total_score">
            <p>{{$t('m.Score')}}</p>
            <p>{{problem.total_score}}</p>
          </li>
        </ul>
      </Card>
    </div>

    <Modal v-model="graphVisible">
      <div id="pieChart-detail">
        <ECharts :options="largePie" :initOptions="largePieInitOpts"></ECharts>
      </div>
      <div slot="footer">
        <Button type="ghost" @click="graphVisible=false">{{$t('m.Close')}}</Button>
      </div>
    </Modal>
  </div>
</template>

<script>
  import {mapGetters, mapActions} from 'vuex'
  import {types} from '../../../../store'
  import CodeMirror from '@oj/components/CodeMirror.vue'
  import storage from '@/utils/storage'
  import {FormMixin} from '@oj/components/mixins'
  import {JUDGE_STATUS, CONTEST_STATUS, buildProblemCodeKey} from '@/utils/constants'
  import api from '@oj/api'
  import {pie, largePie} from './chartData'

  // 只显示这些状态的图形占用
  const filtedStatus = ['-1', '-2', '0', '1', '2', '3', '4', '8']

  export default {
    name: 'Problem',
    components: {
      CodeMirror
    },
    mixins: [FormMixin],
    data () {
      return {
        statusVisible: false,
        captchaRequired: false,
        graphVisible: false,
        submissionExists: false,
        captchaCode: '',
        captchaSrc: '',
        contestID: '',
        problemID: '',
        submitting: false,
        code: '',
        language: 'C',
        theme: 'solarized',
        submissionId: '',
        submitted: false,
        zipFile: null,
        myZip: null,
        zipForm: {
          nim: '',
          name: ''
        },
        result: {
          result: 9
        },
        problem: {
          title: '',
          description: '',
          hint: '',
          my_status: '',
          template: {},
          languages: [],
          samples: [],
          created_by: {
            username: ''
          },
          tags: [],
          io_mode: {'io_mode': 'Standard IO'}
        },
        pie: pie,
        largePie: largePie,
        // echarts 无法获取隐藏dom的大小，需手动指定
        largePieInitOpts: {
          width: '500',
          height: '480'
        }
      }
    },
    beforeRouteEnter (to, from, next) {
      let problemCode = storage.get(buildProblemCodeKey(to.params.problemID, to.params.contestID))
      if (problemCode) {
        next(vm => {
          vm.language = problemCode.language
          vm.code = problemCode.code
          vm.theme = problemCode.theme
        })
      } else {
        next()
      }
    },
    mounted () {
      this.$store.commit(types.CHANGE_CONTEST_ITEM_VISIBLE, {menu: false})
      this.init()
    },
    methods: {
      ...mapActions(['changeDomTitle']),
      init () {
        this.$Loading.start()
        this.contestID = this.$route.params.contestID
        this.problemID = this.$route.params.problemID
        let func = this.$route.name === 'problem-details' ? 'getProblem' : 'getContestProblem'
        api[func](this.problemID, this.contestID).then(res => {
          this.$Loading.finish()
          let problem = res.data.data
          this.changeDomTitle({title: problem.title})
          api.submissionExists(problem.id).then(res => {
            this.submissionExists = res.data.data
          })
          problem.languages = (problem.languages || []).sort()
          this.problem = problem
          this.myZip = problem.my_zip || null
          if (problem.statistic_info) {
            this.changePie(problem)
          }

          // 在beforeRouteEnter中修改了, 说明本地有code，无需加载template
          if (this.code !== '') {
            return
          }
          // try to load problem template
          this.language = this.problem.languages[0] || 'C'
          let template = this.problem.template
          if (template && template[this.language]) {
            this.code = template[this.language]
          }
        }, () => {
          this.$Loading.error()
        })
      },
      changePie (problemData) {
        // 只显示特定的一些状态
        for (let k in problemData.statistic_info) {
          if (filtedStatus.indexOf(k) === -1) {
            delete problemData.statistic_info[k]
          }
        }
        let acNum = problemData.accepted_number
        let data = [
          {name: 'WA', value: problemData.submission_number - acNum},
          {name: 'AC', value: acNum}
        ]
        this.pie.series[0].data = data
        // 只把大图的AC selected下，这里需要做一下deepcopy
        let data2 = JSON.parse(JSON.stringify(data))
        data2[1].selected = true
        this.largePie.series[1].data = data2

        // 根据结果设置legend,没有提交过的legend不显示
        let legend = Object.keys(problemData.statistic_info).map(ele => JUDGE_STATUS[ele].short)
        if (legend.length === 0) {
          legend.push('AC', 'WA')
        }
        this.largePie.legend.data = legend

        // 把ac的数据提取出来放在最后
        let acCount = problemData.statistic_info['0']
        delete problemData.statistic_info['0']

        let largePieData = []
        Object.keys(problemData.statistic_info).forEach(ele => {
          largePieData.push({name: JUDGE_STATUS[ele].short, value: problemData.statistic_info[ele]})
        })
        largePieData.push({name: 'AC', value: acCount})
        this.largePie.series[0].data = largePieData
      },
      handleRoute (route) {
        this.$router.push(route)
      },
      onChangeLang (newLang) {
        if (this.problem.template[newLang]) {
          if (this.code.trim() === '') {
            this.code = this.problem.template[newLang]
          }
        }
        this.language = newLang
      },
      onChangeTheme (newTheme) {
        this.theme = newTheme
      },
      onResetToTemplate () {
        this.$Modal.confirm({
          content: this.$i18n.t('m.Are_you_sure_you_want_to_reset_your_code'),
          onOk: () => {
            let template = this.problem.template
            if (template && template[this.language]) {
              this.code = template[this.language]
            } else {
              this.code = ''
            }
          }
        })
      },
      checkSubmissionStatus () {
        // 使用setTimeout避免一些问题
        if (this.refreshStatus) {
          // 如果之前的提交状态检查还没有停止,则停止,否则将会失去timeout的引用造成无限请求
          clearTimeout(this.refreshStatus)
        }
        const checkStatus = () => {
          let id = this.submissionId
          api.getSubmission(id).then(res => {
            this.result = res.data.data
            if (Object.keys(res.data.data.statistic_info).length !== 0) {
              this.submitting = false
              this.submitted = false
              clearTimeout(this.refreshStatus)
              this.init()
            } else {
              this.refreshStatus = setTimeout(checkStatus, 2000)
            }
          }, res => {
            this.submitting = false
            clearTimeout(this.refreshStatus)
          })
        }
        this.refreshStatus = setTimeout(checkStatus, 2000)
      },
      formatFileSize (bytes) {
        if (!bytes) return '0 B'
        const k = 1024
        const sizes = ['B', 'KB', 'MB', 'GB']
        const i = Math.floor(Math.log(bytes) / Math.log(k))
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
      },
      formatTime (iso) {
        if (!iso) return ''
        const d = new Date(iso)
        if (isNaN(d.getTime())) return iso
        const pad = n => String(n).padStart(2, '0')
        return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
      },
      onZipSelected (event) {
        const file = event.target.files[0] || null
        this.zipFile = file
        if (file) {
          const base = file.name.replace(/\.[^/.]+$/, '')
          const parts = base.split('_')
          if (parts.length >= 2) {
            if (/^\d+$/.test(parts[0])) {
              if (!this.zipForm.nim) this.zipForm.nim = parts[0]
              if (!this.zipForm.name) this.zipForm.name = parts[1].replace(/[-_]/g, ' ')
            }
          }
        }
      },
      submitZip () {
        if (!this.zipFile) {
          this.$error('Pilih berkas zip terlebih dahulu')
          return
        }
        if (!this.zipForm.nim.trim()) {
          this.$error('NIM mahasiswa wajib diisi')
          return
        }
        if (!this.zipForm.name.trim()) {
          this.$error('Nama lengkap mahasiswa wajib diisi')
          return
        }
        this.submitting = true
        api.submitZipAnswer(this.problem.id, this.zipFile, {
          nim: this.zipForm.nim.trim(),
          name: this.zipForm.name.trim()
        }).then(res => {
          this.submitting = false
          if (res.data.error) {
            this.$error(res.data.data)
            return
          }
          this.myZip = res.data.data
          this.$success('Jawaban berkas ZIP berhasil dikumpulkan')
        }, err => {
          this.submitting = false
          const msg = (err.response && err.response.data && err.response.data.data) || 'Jawaban gagal dikumpulkan'
          this.$error(msg)
        })
      },
      submitCode () {
        if (this.code.trim() === '') {
          this.$error(this.$i18n.t('m.Code_can_not_be_empty'))
          return
        }
        this.submissionId = ''
        this.result = {result: 9}
        this.submitting = true
        let data = {
          problem_id: this.problem.id,
          language: this.language,
          code: this.code,
          contest_id: this.contestID
        }
        if (this.captchaRequired) {
          data.captcha = this.captchaCode
        }
        const submitFunc = (data, detailsVisible) => {
          this.statusVisible = true
          api.submitCode(data).then(res => {
            this.submissionId = res.data.data && res.data.data.submission_id
            // 定时检查状态
            this.submitting = false
            this.submissionExists = true
            if (!detailsVisible) {
              this.$Modal.success({
                title: this.$i18n.t('m.Success'),
                content: this.$i18n.t('m.Submit_code_successfully')
              })
              return
            }
            this.submitted = true
            this.checkSubmissionStatus()
          }, res => {
            this.getCaptchaSrc()
            if (res.data.data.startsWith('Captcha is required')) {
              this.captchaRequired = true
            }
            this.submitting = false
            this.statusVisible = false
          })
        }

        if (this.contestRuleType === 'OI' && !this.OIContestRealTimePermission) {
          if (this.submissionExists) {
            this.$Modal.confirm({
              title: '',
              content: '<h3>' + this.$i18n.t('m.You_have_submission_in_this_problem_sure_to_cover_it') + '<h3>',
              onOk: () => {
                // 暂时解决对话框与后面提示对话框冲突的问题(否则一闪而过）
                setTimeout(() => {
                  submitFunc(data, false)
                }, 1000)
              },
              onCancel: () => {
                this.submitting = false
              }
            })
          } else {
            submitFunc(data, false)
          }
        } else {
          submitFunc(data, true)
        }
      },
      onCopy (event) {
        this.$success('Code copied')
      },
      onCopyError (e) {
        this.$error('Failed to copy code')
      },
      downloadPdf () {
        if (this.pdfSource) {
          window.open(this.pdfSource)
        }
      },
      openPdfNewTab () {
        if (this.pdfSource) {
          window.open(this.pdfSource, '_blank')
        }
      }
    },
    computed: {
      ...mapGetters(['problemSubmitDisabled', 'contestRuleType', 'OIContestRealTimePermission', 'contestStatus', 'isAuthenticated', 'profile']),
      sampleExpectedFilename () {
        const pattern = this.problem.answer_filename_template || this.problem.answer_filename || '{NIM}_{NAMA}_soal.zip'
        const nim = (this.zipForm && this.zipForm.nim && this.zipForm.nim.trim()) || '2508394'
        const rawName = (this.zipForm && this.zipForm.name && this.zipForm.name.trim()) || 'Budi Santoso'
        const nameUnderscore = rawName.replace(/\s+/g, '_')
        let res = pattern.replace(/\{(?:nim|username)\}/gi, nim)
        res = res.replace(/\{nama\}/gi, nameUnderscore)
        res = res.replace(/\bnim\b/gi, nim)
        res = res.replace(/\bnama\b/gi, nameUnderscore)
        return res
      },
      pdfSource () {
        if (this.problem.pdf_url) return this.problem.pdf_url
        if (this.problem.template && typeof this.problem.template === 'object' && this.problem.template.pdf_url) {
          return this.problem.template.pdf_url
        }
        if (this.problem.description) {
          const match = this.problem.description.match(/\/public\/upload\/[a-zA-Z0-9_\-.]+\.pdf/i)
          if (match) return match[0]
        }
        return ''
      },
      contest () {
        return this.$store.state.contest.contest
      },
      contestEnded () {
        return this.contestStatus === CONTEST_STATUS.ENDED
      },
      submissionStatus () {
        return {
          text: JUDGE_STATUS[this.result.result]['name'],
          color: JUDGE_STATUS[this.result.result]['color']
        }
      },
      submissionRoute () {
        if (this.contestID) {
          return {name: 'contest-submission-list', query: {problemID: this.problemID}}
        } else {
          return {name: 'submission-list', query: {problemID: this.problemID}}
        }
      }
    },
    beforeRouteLeave (to, from, next) {
      // 防止切换组件后仍然不断请求
      clearInterval(this.refreshStatus)

      this.$store.commit(types.CHANGE_CONTEST_ITEM_VISIBLE, {menu: true})
      storage.set(buildProblemCodeKey(this.problem._id, from.params.contestID), {
        code: this.code,
        language: this.language,
        theme: this.theme
      })
      next()
    },
    watch: {
      '$route' () {
        this.init()
      }
    }
  }
</script>

<style lang="less" scoped>
  .card-title {
    margin-left: 8px;
  }

  .flex-container {
    #problem-main {
      flex: auto;
      margin-right: 18px;
    }
    #right-column {
      flex: none;
      width: 220px;
    }
  }

  #problem-content {
    margin-top: -50px;
    .title {
      font-size: 20px;
      font-weight: 400;
      margin: 25px 0 8px 0;
      color: #3091f2;
      .copy {
        padding-left: 8px;
      }
    }
    p.content {
      margin-left: 25px;
      margin-right: 20px;
      font-size: 15px
    }
    .sample {
      align-items: stretch;
      &-input, &-output {
        width: 50%;
        flex: 1 1 auto;
        display: flex;
        flex-direction: column;
        margin-right: 5%;
      }
      pre {
        flex: 1 1 auto;
        align-self: stretch;
        border-style: solid;
        background: transparent;
      }
    }
  }

  #submit-code {
    margin-top: 20px;
    margin-bottom: 20px;
    .status {
      float: left;
      span {
        margin-right: 10px;
        margin-left: 10px;
      }
    }
    .captcha-container {
      display: inline-block;
      .captcha-code {
        width: auto;
        margin-top: -20px;
        margin-left: 20px;
      }
    }
  }

  #info {
    margin-bottom: 20px;
    margin-top: 20px;
    ul {
      list-style-type: none;
      li {
        border-bottom: 1px dotted #e9eaec;
        margin-bottom: 10px;
        p {
          display: inline-block;
        }
        p:first-child {
          width: 90px;
        }
        p:last-child {
          float: right;
        }
      }
    }
  }

  .fl-right {
    float: right;
  }

  #pieChart {
    .echarts {
      height: 250px;
      width: 210px;
    }
    #detail {
      position: absolute;
      right: 10px;
      top: 10px;
    }
  }

  #pieChart-detail {
    margin-top: 20px;
    width: 500px;
    height: 480px;
  }
</style>
