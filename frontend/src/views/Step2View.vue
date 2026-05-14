<script setup>
import { onMounted, ref } from 'vue'
import { useStoryboardStore } from '../stores/storyboard'
import { useProjectStore } from '../stores/project'
import StrategyPanel from '../components/step2/StrategyPanel.vue'
import ShotItem from '../components/step2/ShotItem.vue'
import { Sparkles, Loader2, Film, Download, Check, Eye } from 'lucide-vue-next'

const storyboardStore = useStoryboardStore()
const projectStore = useProjectStore()
const isDownloading = ref(false)

// 如果没有数据，加载mock数据
onMounted(() => {
  if (storyboardStore.shots.length === 0) {
    storyboardStore.setMockData()
  }
})

// 生成剩余分镜
const generateRemaining = async () => {
  try {
    await storyboardStore.generateRemaining({
        ...projectStore.config,
        autoGenerateImage: true
    })
  } catch (error) {
    console.error('生成剩余分镜失败:', error)
  }
}

// 合并视频
const handleMergeVideos = async () => {
  try {
    await storyboardStore.mergeAllVideos()
  } catch (error) {
    alert(error.message)
  }
}

// 预览视频
const previewVideo = () => {
  if (!storyboardStore.mergedVideoUrl) return
  window.open(storyboardStore.getUploadUrl(storyboardStore.mergedVideoUrl), '_blank')
}

// 下载视频
const downloadVideo = async () => {
  if (!storyboardStore.mergedVideoUrl || isDownloading.value) return
  
  isDownloading.value = true
  try {
    const url = storyboardStore.getUploadUrl(storyboardStore.mergedVideoUrl)
    const response = await fetch(url)
    if (!response.ok) throw new Error('Download failed')
    
    const blob = await response.blob()
    const blobUrl = window.URL.createObjectURL(blob)
    
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = `storyboard_video_${Date.now()}.mp4`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(blobUrl)
  } catch (error) {
    console.error('Download error:', error)
    alert('下载失败，请尝试预览视频后手动保存')
  } finally {
    isDownloading.value = false
  }
}
</script>

<template>
  <div class="h-full flex flex-col lg:flex-row">
    <!-- 加载遮罩 - 生成第一个分镜 -->
    <div 
      v-if="storyboardStore.isGeneratingFirst" 
      class="absolute inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center"
    >
      <div class="text-center">
        <Loader2 class="animate-spin text-teal-400 mx-auto mb-4" :size="48" />
        <p class="text-slate-300 text-lg">AI 正在生成开场分镜...</p>
        <p class="text-slate-500 text-sm mt-2">请稍候，预计5-8秒</p>
      </div>
    </div>

    <!-- 加载遮罩 - 重新策划分镜 -->
    <div 
      v-if="storyboardStore.isRegenerating" 
      class="absolute inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center"
    >
      <div class="text-center">
        <Loader2 class="animate-spin text-orange-400 mx-auto mb-4" :size="48" />
        <p class="text-slate-300 text-lg">AI 正在重新策划分镜...</p>
        <p class="text-slate-500 text-sm mt-2">根据您的建议调整脚本内容</p>
      </div>
    </div>

    <!-- 加载遮罩 - 通用加载 -->
    <div 
      v-if="storyboardStore.isLoading && !storyboardStore.isGeneratingFirst && !storyboardStore.isRegenerating" 
      class="absolute inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center"
    >
      <div class="text-center">
        <Loader2 class="animate-spin text-slate-400 mx-auto mb-4" :size="48" />
        <p class="text-slate-300 text-lg">请稍候...</p>
      </div>
    </div>
    
    <!-- 加载遮罩 - 合并视频 -->
    <div 
      v-if="storyboardStore.isMerging" 
      class="absolute inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center"
    >
      <div class="text-center">
        <Loader2 class="animate-spin text-purple-400 mx-auto mb-4" :size="48" />
        <p class="text-slate-300 text-lg">正在合并视频...</p>
        <p class="text-slate-500 text-sm mt-2">将所有分镜组合为完整视频</p>
      </div>
    </div>

    <!-- 左侧栏：分析与设置 -->
    <div class="w-full lg:w-1/4 bg-slate-900 border-r border-slate-800 p-6 overflow-y-auto custom-scrollbar z-10 shrink-0">
      <StrategyPanel />
      
      <!-- 底部设置 -->
      <div class="mt-8 pt-6 border-t border-slate-800">
        <div class="flex items-center justify-between text-xs text-slate-500 mb-2">
          <span>VOICE MODEL</span>
          <span class="text-purple-400">Puck (Locked)</span>
        </div>
        <div class="flex items-center justify-between text-xs text-slate-500">
          <span>RESOLUTION</span>
          <span class="text-teal-400">RES 2K</span>
        </div>
      </div>
    </div>

    <!-- 右侧栏：脚本列表 -->
    <div class="w-full lg:w-3/4 bg-slate-950 p-6 lg:p-10 overflow-y-auto custom-scrollbar">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-bold text-white flex items-center gap-2">
          分镜脚本 <span class="bg-slate-800 text-slate-400 text-xs px-2 py-0.5 rounded-full">共 {{ storyboardStore.shots.length }} 个镜头</span>
        </h2>
        
        <div class="flex items-center gap-2">
          <!-- 生成剩余分镜按钮 -->
          <button 
            v-if="storyboardStore.hasFirstShot && storyboardStore.shots.length === 1"
            @click="generateRemaining"
            :disabled="storyboardStore.isGeneratingRemaining"
            class="bg-teal-600 hover:bg-teal-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white text-xs font-bold px-4 py-2 rounded-lg transition-colors shadow-lg shadow-teal-500/10 flex items-center gap-2"
          >
            <Loader2 v-if="storyboardStore.isGeneratingRemaining" class="animate-spin" :size="14" />
            <Sparkles v-else :size="14" />
            {{ storyboardStore.isGeneratingRemaining ? '生成中...' : '基于分镜1生成剩余全部' }}
          </button>
          
          <!-- 已生成全部提示 -->
          <span 
            v-if="storyboardStore.shots.length > 1 && !storyboardStore.isGeneratingRemaining" 
            class="bg-slate-800 border border-slate-700 text-slate-400 text-xs px-3 py-2 rounded-lg flex items-center gap-1.5"
          >
            <Check :size="12" class="text-green-500" /> 已生成全部分镜
          </span>
          
          <!-- 生成完整视频按钮 -->
          <button 
            v-if="storyboardStore.shots.length > 1"
            @click="handleMergeVideos"
            :disabled="storyboardStore.isMerging"
            class="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white text-xs font-bold px-4 py-2 rounded-lg transition-colors shadow-lg shadow-indigo-500/10 flex items-center gap-2"
          >
            <Loader2 v-if="storyboardStore.isMerging" class="animate-spin" :size="14" />
            <Film v-else :size="14" />
            {{ storyboardStore.isMerging ? '合并中...' : '生成完整视频' }}
          </button>

          <!-- 预览完整视频按钮 -->
          <button 
            v-if="storyboardStore.mergedVideoUrl"
            @click="previewVideo"
            class="bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold px-4 py-2 rounded-lg transition-colors shadow-lg shadow-blue-500/10 flex items-center gap-2 animate-in fade-in slide-in-from-right-4"
          >
            <Eye :size="14" />
            预览视频
          </button>

          <!-- 下载完整视频按钮 -->
          <button 
            v-if="storyboardStore.mergedVideoUrl"
            @click="downloadVideo"
            :disabled="isDownloading"
            class="bg-green-600 hover:bg-green-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white text-xs font-bold px-4 py-2 rounded-lg transition-colors shadow-lg shadow-green-500/10 flex items-center gap-2 animate-in fade-in slide-in-from-right-4"
          >
            <Loader2 v-if="isDownloading" class="animate-spin" :size="14" />
            <Download v-else :size="14" />
            {{ isDownloading ? '下载中...' : '下载视频' }}
          </button>
        </div>
      </div>

      <!-- 生成中提示 -->
      <div v-if="storyboardStore.isGeneratingRemaining" class="mb-6 bg-teal-900/30 border border-teal-800/50 rounded-lg p-4">
        <div class="flex items-center gap-3">
          <Loader2 class="animate-spin text-teal-400" :size="20" />
          <div>
            <p class="text-teal-300 text-sm font-medium">正在生成剩余分镜...</p>
            <p class="text-teal-500 text-xs mt-1">基于第一个分镜内容，AI正在创作后续镜头</p>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="storyboardStore.shots.length === 0" class="text-center py-20">
        <div class="text-slate-500 text-lg mb-4">暂无分镜数据</div>
        <p class="text-slate-600 text-sm">请返回上一步配置产品信息并启动AI生成</p>
      </div>

      <div v-else class="space-y-4 pb-20">
        <ShotItem 
          v-for="(shot, idx) in storyboardStore.shots" 
          :key="shot.id" 
          :index="idx" 
          :shot="shot" 
          :is-expanded="storyboardStore.expandedIndex === idx" 
          @toggle="storyboardStore.toggleShot(idx)"
        />
      </div>
    </div>
  </div>
</template>

