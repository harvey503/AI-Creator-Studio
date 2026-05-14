<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'
import { useStoryboardStore } from '../stores/storyboard'
import { Globe, Settings, Upload, Image, Video, Maximize2, Sparkles, Loader2, X } from 'lucide-vue-next'
import FileUploader from '../components/common/FileUploader.vue'
import { getUploadUrl } from '../api/client'

const router = useRouter()
const projectStore = useProjectStore()
const storyboardStore = useStoryboardStore()

const isGenerating = ref(false)
const errorMessage = ref('')

// 产品图片列表
const productImages = computed({
  get: () => projectStore.assets.productImages,
  set: (val) => projectStore.setProductImages(val)
})

// 模特图片列表
const modelImages = computed({
  get: () => projectStore.assets.modelImages,
  set: (val) => projectStore.setModelImages(val)
})

// 参考视频
const referenceVideo = computed(() => projectStore.assets.referenceVideo)

// 上传参考视频
const handleVideoUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  try {
    await projectStore.uploadReference(file)
  } catch (error) {
    errorMessage.value = error.message || '视频上传失败'
  }
}

// 删除参考视频
const removeVideo = async () => {
  try {
    await projectStore.deleteReference()
  } catch (error) {
    console.error('删除视频失败:', error)
  }
}

const startGeneration = async () => {
  // 验证必填字段
  if (!projectStore.config.productName.trim()) {
    errorMessage.value = '请输入产品标题'
    return
  }
  
  errorMessage.value = ''
  isGenerating.value = true
  
  try {
    // 优化：只快速生成第一个分镜（5-8秒），而不是生成全部（40秒+）
    await storyboardStore.generateFirstShotOnly(projectStore.config)
    router.push('/generate')
  } catch (error) {
    errorMessage.value = error.message || '生成失败，请重试'
    // 如果API失败，使用mock数据演示
    storyboardStore.setMockData()
    router.push('/generate')
  } finally {
    isGenerating.value = false
  }
}
</script>

<template>
  <div class="h-full overflow-y-auto p-8 max-w-7xl mx-auto">
    <div class="grid grid-cols-12 gap-8">
      <!-- 左侧表单 -->
      <div class="col-span-12 lg:col-span-5 space-y-6">
        <div class="space-y-2">
          <label class="text-xs font-bold text-slate-500 uppercase flex items-center gap-2">
            <Globe :size="14" /> 目标市场 / Target Market
          </label>
          <select 
            v-model="projectStore.config.market"
            class="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-sm focus:ring-2 focus:ring-teal-500 outline-none text-slate-300"
          >
            <option value="US">United States (美国)</option>
            <option value="UK">United Kingdom (英国)</option>
          </select>
        </div>

        <div class="space-y-2">
          <label class="text-xs font-bold text-slate-500 uppercase">产品标题 (必填)</label>
          <input 
            type="text" 
            v-model="projectStore.config.productName"
            placeholder="例如：亚马逊爆款无叶挂脖风扇..." 
            class="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-sm focus:ring-2 focus:ring-teal-500 outline-none placeholder-slate-600 text-slate-300"
          />
        </div>

        <div class="space-y-2">
          <label class="text-xs font-bold text-slate-500 uppercase">产品描述 / 卖点 (可选)</label>
          <textarea 
            rows="4"
            v-model="projectStore.config.productDesc"
            placeholder="粘贴亚马逊五点描述或用户评论..." 
            class="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-sm focus:ring-2 focus:ring-teal-500 outline-none placeholder-slate-600 resize-none text-slate-300"
          ></textarea>
        </div>

        <div class="space-y-2">
          <label class="text-xs font-bold text-slate-500 uppercase">创意想法 (可选)</label>
          <textarea 
            rows="3"
            v-model="projectStore.config.creativeIdea"
            placeholder="逐帧复刻，更强的钩子。需要换一个模特、换一个场景..." 
            class="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-sm focus:ring-2 focus:ring-teal-500 outline-none placeholder-slate-600 resize-none text-slate-300"
          ></textarea>
        </div>

        <!-- 底部参数栏 -->
        <div class="bg-slate-800/50 p-4 rounded-xl border border-slate-700 space-y-4">
          <div class="flex items-center gap-2 text-teal-400 font-semibold text-sm">
            <Settings :size="16" /> 视频参数
          </div>
          <div class="grid grid-cols-2 gap-4">
            <!-- Row 1 -->
            <div>
              <label class="block text-xs text-slate-500 mb-1">画面比例</label>
              <select 
                v-model="projectStore.config.aspectRatio"
                class="w-full bg-slate-900 border border-slate-700 rounded p-2 text-xs text-slate-300 focus:border-teal-500 outline-none"
              >
                <option value="9:16">9:16 (竖屏通用)</option>
                <option value="16:9">16:9 (横屏)</option>
                <option value="1:1">1:1 (方形)</option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-slate-500 mb-1">生成模式</label>
              <select 
                v-model="projectStore.config.generationMode"
                class="w-full bg-slate-900 border border-slate-700 rounded p-2 text-xs text-slate-300 focus:border-teal-500 outline-none"
              >
                <option value="first_frame">首帧图 (仅生成首图)</option>
              </select>
            </div>

            <!-- Row 2 -->
            <div>
              <label class="block text-xs text-slate-500 mb-1">分辨率</label>
              <select 
                v-model="projectStore.config.resolution"
                class="w-full bg-slate-900 border border-slate-700 rounded p-2 text-xs text-slate-300 focus:border-teal-500 outline-none"
              >
                <option value="720p">720p (普通)</option>
                <option value="1080P">1080P (标清)</option>
                <option value="2K">2K (高清 - 推荐)</option>
                <option value="4K">4K (超高清)</option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-slate-500 mb-1">分镜数量 ({{ projectStore.config.shotCount }})</label>
              <div class="flex items-center bg-slate-900 border border-slate-700 rounded overflow-hidden h-[34px]">
                <button 
                  @click="projectStore.config.shotCount > 2 && projectStore.config.shotCount--"
                  class="px-3 hover:bg-slate-800 text-slate-400 transition-colors disabled:opacity-50"
                  :disabled="projectStore.config.shotCount <= 2"
                >-</button>
                <div class="flex-1 text-center text-xs text-slate-300 font-mono">
                  {{ projectStore.config.shotCount }}
                </div>
                <button 
                  @click="projectStore.config.shotCount < 6 && projectStore.config.shotCount++"
                  class="px-3 hover:bg-slate-800 text-slate-400 transition-colors disabled:opacity-50"
                  :disabled="projectStore.config.shotCount >= 6"
                >+</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧素材上传 -->
      <div class="col-span-12 lg:col-span-7 space-y-6">
        <!-- 产品图 -->
        <div class="space-y-2">
          <label class="text-xs font-bold text-slate-500 uppercase flex items-center justify-between">
            <span>指定产品 (可选)</span>
            <span class="text-slate-600 font-normal text-[10px]">上传1-5张素材图，提取特征用于所有镜头</span>
          </label>
          <FileUploader
            v-model="productImages"
            :max-files="5"
            :placeholders="5"
            accept="image/*"
            :upload-fn="projectStore.uploadProduct"
            :delete-fn="projectStore.deleteProductImage"
          />
        </div>

        <!-- 模特与参考 -->
        <div class="grid grid-cols-2 gap-6">
          <div class="space-y-2">
            <label class="text-xs font-bold text-slate-500 uppercase flex items-center gap-2">
              <Image :size="14" /> 指定模特 (可选)
            </label>
            <FileUploader
              v-model="modelImages"
              :max-files="3"
              :placeholders="3"
              accept="image/*"
              :upload-fn="projectStore.uploadModel"
              :delete-fn="projectStore.deleteModelImage"
            />
          </div>

          <div class="space-y-2">
            <label class="text-xs font-bold text-slate-500 uppercase flex items-center gap-2">
              <Video :size="14" /> 参考视频 (可选)
            </label>
            <!-- 已上传视频 -->
            <div v-if="referenceVideo" class="h-24 bg-slate-800 rounded-lg border border-teal-500/30 overflow-hidden relative group">
              <video 
                :src="getUploadUrl(referenceVideo.url)" 
                class="w-full h-full object-cover opacity-80"
              />
              <button 
                @click="removeVideo"
                class="absolute top-1 right-1 bg-red-500 hover:bg-red-400 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X :size="12" />
              </button>
              <div class="absolute top-2 left-2 bg-teal-500 text-slate-900 text-[10px] font-bold px-1.5 py-0.5 rounded shadow-sm">REF</div>
            </div>
            <!-- 上传按钮 -->
            <label v-else class="h-24 bg-slate-800/50 rounded-lg border border-slate-700 border-dashed flex items-center justify-center text-slate-600 hover:text-slate-400 hover:border-slate-500 cursor-pointer transition-colors duration-200">
              <input 
                type="file" 
                accept="video/*"
                @change="handleVideoUpload"
                class="hidden"
              />
              <div class="flex flex-col items-center gap-1">
                <Upload :size="18" />
                <span class="text-[10px]">上传视频</span>
              </div>
            </label>
          </div>
        </div>

        <!-- 错误提示 -->
        <div v-if="errorMessage" class="pt-4">
          <div class="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
            {{ errorMessage }}
          </div>
        </div>

        <!-- 启动按钮 -->
        <div class="pt-8">
          <button 
            @click="startGeneration"
            :disabled="isGenerating"
            class="w-full py-4 bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-400 hover:to-blue-400 disabled:from-slate-600 disabled:to-slate-600 text-slate-900 disabled:text-slate-400 font-bold text-lg rounded-xl shadow-lg shadow-teal-500/20 disabled:shadow-none transition-all active:scale-[0.99] disabled:active:scale-100 flex items-center justify-center gap-2 group"
          >
            <Loader2 v-if="isGenerating" class="animate-spin" :size="20" />
            <Sparkles v-else class="animate-pulse group-hover:rotate-12 transition-transform" />
            {{ isGenerating ? 'AI 正在分析生成中...' : '启动 AI 智能创作流' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
