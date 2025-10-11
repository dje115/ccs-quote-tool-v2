<template>
  <div id="app">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>CCS Admin Portal</h1>
          <el-button @click="logout" type="danger" plain>
            <el-icon><SwitchButton /></el-icon>
            Logout
          </el-button>
        </div>
      </el-header>
      <el-container>
        <el-aside width="250px">
          <el-menu
            :default-active="$route.path"
            class="sidebar-menu"
            router
          >
            <el-menu-item index="/dashboard">
              <el-icon><House /></el-icon>
              <span>Dashboard</span>
            </el-menu-item>
            <el-menu-item index="/tenants">
              <el-icon><OfficeBuilding /></el-icon>
              <span>Tenants</span>
            </el-menu-item>
            <el-menu-item index="/users">
              <el-icon><User /></el-icon>
              <span>Users</span>
            </el-menu-item>
            <el-menu-item index="/api-keys">
              <el-icon><Key /></el-icon>
              <span>Global API Keys</span>
            </el-menu-item>
            <el-menu-item index="/settings">
              <el-icon><Setting /></el-icon>
              <span>System Settings</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
export default {
  name: 'App',
  methods: {
    logout() {
      localStorage.removeItem('admin_token')
      this.$router.push('/login')
    }
  }
}
</script>

<style>
#app {
  height: 100vh;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.header-content h1 {
  margin: 0;
  color: white;
}

.el-header {
  background-color: #409EFF;
  color: white;
  padding: 0 20px;
}

.sidebar-menu {
  height: 100%;
  border-right: 1px solid #e6e6e6;
}

.el-main {
  padding: 20px;
  background-color: #f5f5f5;
}
</style>


