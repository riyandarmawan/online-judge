<template>
</template>

<script>
  import api from '../../api.js'

  export default {
    mounted () {
      const finishLogout = () => {
        this.$store.dispatch('clearProfile')
        this.$router.replace({
          path: '/'
        })
      }

      api.logout().then(finishLogout, finishLogout)
    }
  }
</script>
