<template>
  <div>
    <Form ref="formLogin" :model="formLogin" :rules="ruleLogin">
      <FormItem prop="nim">
        <Input type="text" v-model="formLogin.nim" placeholder="NIM" size="large" @on-enter="handleLogin">
        <Icon type="ios-person-outline" slot="prepend"></Icon>
        </Input>
      </FormItem>
      <FormItem prop="name">
        <Input type="text" v-model="formLogin.name" placeholder="Nama lengkap" size="large" @on-enter="handleLogin">
        <Icon type="ios-contact-outline" slot="prepend"></Icon>
        </Input>
      </FormItem>
      <FormItem prop="password">
        <Input type="password" v-model="formLogin.password" placeholder="Password / PIN" size="large" @on-enter="handleLogin">
        <Icon type="ios-locked-outline" slot="prepend"></Icon>
        </Input>
      </FormItem>
    </Form>

    <div style="font-size: 12px; color: #808695; line-height: 1.5; margin-bottom: 16px; background: #f8fbfd; padding: 10px 12px; border-radius: 4px; border: 1px solid #e8eaec;">
      <Icon type="information-circled" style="color: #2d8cf0; margin-right: 4px;"></Icon>
      <b>Catatan:</b> Jika baru pertama kali masuk, buat Password/PIN Anda di atas. Untuk masuk berikutnya, gunakan Password/PIN yang sama.
    </div>

    <div class="footer">
      <Button
        type="primary"
        @click="handleLogin"
        class="btn" long
        :loading="btnLoginLoading">
        Masuk
      </Button>
    </div>
  </div>
</template>

<script>
  import { mapGetters, mapActions } from 'vuex'
  import api from '@oj/api'
  import { FormMixin } from '@oj/components/mixins'

  export default {
    mixins: [FormMixin],
    data () {
      return {
        btnLoginLoading: false,
        formLogin: {
          nim: '',
          name: '',
          password: ''
        },
        ruleLogin: {
          nim: [
            {required: true, trigger: 'blur', message: 'NIM wajib diisi'}
          ],
          name: [
            {required: true, trigger: 'blur', message: 'Nama lengkap wajib diisi'}
          ],
          password: [
            {required: true, trigger: 'blur', message: 'Password/PIN wajib diisi'},
            {min: 3, trigger: 'blur', message: 'Password/PIN minimal 3 karakter'}
          ]
        }
      }
    },
    methods: {
      ...mapActions(['changeModalStatus', 'getProfile']),
      handleLogin () {
        this.validateForm('formLogin').then(valid => {
          this.btnLoginLoading = true
          api.studentLogin(this.formLogin).then(res => {
            this.btnLoginLoading = false
            this.changeModalStatus({visible: false})
            this.getProfile()
            this.$success('Berhasil masuk')
          }, _ => {
            this.btnLoginLoading = false
          })
        })
      }
    },
    computed: {
      ...mapGetters(['website', 'modalStatus']),
      visible: {
        get () {
          return this.modalStatus.visible
        },
        set (value) {
          this.changeModalStatus({visible: value})
        }
      }
    }
  }
</script>

<style scoped lang="less">
  .footer {
    overflow: auto;
    margin-top: 20px;
    margin-bottom: -15px;
    text-align: left;
    .btn {
      margin: 0 0 15px 0;
      &:last-child {
        margin: 0;
      }
    }
  }
</style>
