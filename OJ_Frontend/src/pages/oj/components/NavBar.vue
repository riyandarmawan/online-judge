<template>
  <div id="header">
    <Menu theme="light" mode="horizontal" @on-select="handleRoute" :active-name="activeMenu" class="oj-menu">
      <div class="logo"><span>{{website.website_name}}</span></div>
      <Menu-item name="/">
        <Icon type="home"></Icon>
        {{$t('m.Home')}}
      </Menu-item>
      <Menu-item name="/problem">
        <Icon type="ios-keypad"></Icon>
        {{$t('m.NavProblems')}}
      </Menu-item>
      <Menu-item name="/status">
        <Icon type="ios-pulse-strong"></Icon>
        Pengumpulan
      </Menu-item>
      <Menu-item v-if="hasJudgeSession" name="/oi-rank">
        <Icon type="podium"></Icon>
        Peringkat
      </Menu-item>
      <template v-if="!isAuthenticated">
        <div class="btn-menu">
          <Button type="ghost"
                  ref="loginBtn"
                  shape="circle"
                  @click="handleBtnClick('login')">{{$t('m.Login')}}
          </Button>
        </div>
      </template>
      <template v-else>
        <Dropdown class="drop-menu" @on-click="handleRoute" placement="bottom" trigger="click">
          <Button type="text" class="drop-menu-title">{{ user.username }}
            <Icon type="arrow-down-b"></Icon>
          </Button>
          <Dropdown-menu slot="list">
            <Dropdown-item name="/status?myself=1">{{$t('m.MySubmissions')}}</Dropdown-item>
            <Dropdown-item divided name="/logout">{{$t('m.Logout')}}</Dropdown-item>
          </Dropdown-menu>
        </Dropdown>
      </template>
    </Menu>
    <Modal v-model="modalVisible" :width="400">
      <div slot="header" class="modal-title">{{$t('m.Welcome_to')}} {{website.website_name}}</div>
      <component :is="modalStatus.mode" v-if="modalVisible"></component>
      <div slot="footer" style="display: none"></div>
    </Modal>
  </div>
</template>

<script>
  import { mapGetters, mapActions } from 'vuex'
  import login from '@oj/views/user/Login'
  import api from '@oj/api'
  export default {
    components: {login},
    data () {
      return {
        hasJudgeSession: false
      }
    },
    mounted () {
      this.getProfile()
      this.refreshRankVisibility()
    },
    methods: {
      ...mapActions(['getProfile', 'changeModalStatus']),
      refreshRankVisibility () {
        if (!this.isAuthenticated) {
          this.hasJudgeSession = false
          return
        }
        api.getExamStatus().then(res => {
          const sessions = res.data.data.unlocked || []
          this.hasJudgeSession = sessions.some(session => session.mode === 'judge')
        }, () => {
          this.hasJudgeSession = false
        })
      },
      handleRoute (route) {
        if (route) {
          this.$router.push(route)
        }
      },
      handleBtnClick (mode) {
        this.changeModalStatus({
          visible: true,
          mode: mode
        })
      }
    },
    computed: {
      ...mapGetters(['website', 'modalStatus', 'user', 'isAuthenticated']),
      // 跟随路由变化
      activeMenu () {
        return '/' + this.$route.path.split('/')[1]
      },
      modalVisible: {
        get () {
          return this.modalStatus.visible
        },
        set (value) {
          this.changeModalStatus({visible: value})
        }
      }
    },
    watch: {
      '$route' () {
        this.refreshRankVisibility()
      },
      isAuthenticated () {
        this.refreshRankVisibility()
      }
    }
  }
</script>

<style lang="less" scoped>
  #header {
    min-width: 300px;
    position: fixed;
    top: 0;
    left: 0;
    height: auto;
    width: 100%;
    z-index: 1000;
    background-color: #fff;
    box-shadow: 0 1px 5px 0 rgba(0, 0, 0, 0.1);
    .oj-menu {
      background: #fdfdfd;
    }

    .logo {
      margin-left: 2%;
      margin-right: 2%;
      font-size: 20px;
      float: left;
      line-height: 60px;
    }

    .drop-menu {
      float: right;
      margin-right: 30px;
      position: absolute;
      right: 10px;
      &-title {
        font-size: 18px;
      }
    }
    .btn-menu {
      font-size: 16px;
      float: right;
      margin-right: 10px;
    }
  }

  .modal {
    &-title {
      font-size: 18px;
      font-weight: 600;
    }
  }
</style>
