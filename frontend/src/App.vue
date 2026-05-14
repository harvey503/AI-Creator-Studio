<script setup>
import { RouterView, useRouter, useRoute } from 'vue-router'
import { Sparkles } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()

const navigateTo = (step) => {
  if (step === 1) {
    router.push('/')
  } else {
    router.push('/generate')
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-slate-300 font-sans overflow-hidden">
    <!-- 头部导航 -->
    <header class="flex items-center justify-between px-6 py-4 bg-slate-900 border-b border-slate-800 text-white z-50 relative">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 bg-gradient-to-br from-teal-400 to-blue-600 rounded-lg flex items-center justify-center font-bold shadow-lg shadow-teal-500/20">
          AI
        </div>
        <span class="text-lg font-semibold tracking-wide text-slate-200">Creator Studio</span>
        <span class="text-slate-500 text-sm ml-2 hidden sm:inline-block">/ 爆款视频创作系统</span>
      </div>

      <div class="flex bg-slate-800 rounded-full p-1">
        <button 
          @click="navigateTo(1)"
          class="px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-300"
          :class="route.name === 'step1' ? 'bg-teal-500 text-slate-900 shadow-lg' : 'text-slate-400 hover:text-white'"
        >
          1. 产品设置
        </button>
        <button 
          @click="navigateTo(2)"
          class="px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-300 flex items-center gap-1"
          :class="route.name === 'step2' ? 'bg-teal-500 text-slate-900 shadow-lg' : 'text-slate-400 hover:text-white'"
        >
          <Sparkles :size="14" />
          2. 智能生成
        </button>
      </div>

      <div class="flex items-center gap-4">
        <div class="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs border border-slate-600">
          JD
        </div>
      </div>
    </header>

    <!-- 主要内容区域 -->
    <main class="h-[calc(100vh-64px)] w-full overflow-hidden">
      <RouterView v-slot="{ Component }">
        <transition enter-active-class="animate-fade-in">
          <component :is="Component" />
        </transition>
      </RouterView>
    </main>
  </div>
</template>
