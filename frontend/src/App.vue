<template>
  <div class="app-container">
    <!-- 移动端顶栏 -->
    <div class="mobile-topbar">
      <button class="hamburger" @click="sidebarOpen = !sidebarOpen">
        <el-icon size="22"><Menu /></el-icon>
      </button>
      <span class="mobile-topbar-title">X 博主监控</span>
    </div>

    <div class="sidebar-overlay" :class="{ 'is-open': sidebarOpen }" @click="sidebarOpen = false" />

    <div class="sidebar" :class="{ 'is-open': sidebarOpen }">
      <div class="logo">
        <el-icon style="margin-right:8px;font-size:22px"><Platform /></el-icon>
        <span>X 博主监控</span>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        background-color="transparent"
        text-color="#bfcbd9"
        active-text-color="#409eff"
        @select="sidebarOpen = false"
      >
        <el-menu-item index="/monitor">
          <el-icon><Monitor /></el-icon>
          <span>博主监控</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </div>

    <div class="main-content">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { loadTimezone } from './lib/timezone'
const sidebarOpen = ref(false)
onMounted(loadTimezone)
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #f5f7fa;
  color: #303133;
}

.app-container {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 200px;
  background: #1a1d2e;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0; left: 0; bottom: 0;
  z-index: 100;
  transition: transform 0.25s;
}

.logo {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}

.el-menu { border-right: none !important; padding: 8px 0; }
.el-menu-item { border-radius: 6px; margin: 2px 8px; }

.main-content {
  margin-left: 200px;
  flex: 1;
  padding: 24px;
  min-height: 100vh;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-header h2 { margin: 0; font-size: 20px; }

.mobile-topbar { display: none; }
.sidebar-overlay { display: none; }

@media (max-width: 768px) {
  .mobile-topbar {
    display: flex;
    align-items: center;
    gap: 12px;
    height: 48px;
    padding: 0 16px;
    background: #1a1d2e;
    color: #fff;
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 200;
  }
  .mobile-topbar-title { font-weight: 600; }
  .hamburger {
    background: none; border: none; color: #fff; cursor: pointer;
    display: flex; align-items: center;
  }
  .sidebar {
    transform: translateX(-100%);
    top: 48px;
  }
  .sidebar.is-open { transform: translateX(0); }
  .sidebar-overlay {
    display: block;
    position: fixed; inset: 0; z-index: 99;
    background: rgba(0,0,0,0.4);
    opacity: 0; pointer-events: none; transition: opacity 0.25s;
  }
  .sidebar-overlay.is-open { opacity: 1; pointer-events: all; }
  .main-content { margin-left: 0; padding: 12px; padding-top: 60px; }
}
</style>
