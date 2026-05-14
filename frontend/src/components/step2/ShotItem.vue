<script setup>
import { computed, ref } from 'vue'
import { useStoryboardStore } from '../../stores/storyboard'
import { ChevronDown, Image, Play, Video, Sparkles, Copy, FileJson, RefreshCw, Loader2, Check, Wand2, Film, Mic } from 'lucide-vue-next'

const props = defineProps({
  index: {
    type: Number,
    required: true
  },
  shot: {
    type: Object,
    required: true
  },
  isExpanded: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['toggle'])

const storyboardStore = useStoryboardStore()

const isRegenerating = ref(false)
const isGeneratingImage = computed(() => storyboardStore.isGeneratingImage(props.shot.id))
const isGeneratingVideo = ref(false)
const copySuccess = ref(false)

const updateField = (field, value) => {
  storyboardStore.updateShot(props.index, field, value)
}

const copyPrompt = async () => {
  try {
    await navigator.clipboard.writeText(props.shot.prompt)
    copySuccess.value = true
    setTimeout(() => { copySuccess.value = false }, 2000)
  } catch (err) {
    console.error('复制失败:', err)
  }
}

const copyManifest = async () => {
  try {
    await navigator.clipboard.writeText(props.shot.manifest)
  } catch (err) {
    console.error('复制失败:', err)
  }
}

const handleRegenerate = async () => {
  isRegenerating.value = true
  try {
    await storyboardStore.regenerate(props.shot.id)
  } catch (err) {
    console.error('重生成失败:', err)
  } finally {
    isRegenerating.value = false
  }
}

const handleGenerateImage = async () => {
  try {
    await storyboardStore.generateImageForShot(props.shot.id)
  } catch (err) {
    console.error('生成图像失败:', err)
  }
}

const handleGenerateVideo = async () => {
  isGeneratingVideo.value = true
  try {
    await storyboardStore.generateVideoForShot(props.shot.id)
  } catch (err) {
    console.error('生成视频失败:', err)
  } finally {
    isGeneratingVideo.value = false
  }
}

const handleVideoError = (e) => {
  console.error('视频加载失败:', e)
}
</script>

<template>
  <div 
    class="border rounded-xl transition-all duration-300 overflow-hidden"
    :class="isExpanded ? 'bg-slate-800/80 border-teal-500/50 shadow-2xl shadow-black/50' : 'bg-slate-800/30 border-slate-700 hover:border-slate-600'"
  >
    <!-- 头部摘要行 -->
    <div 
      @click="emit('toggle')" 
      class="flex items-center justify-between p-4 cursor-pointer select-none"
    >
      <div class="flex items-center gap-4 flex-1 overflow-hidden">
        <div 
          class="px-2 py-1 rounded text-xs font-bold uppercase tracking-wider transition-colors shrink-0"
          :class="isExpanded ? 'bg-teal-500 text-slate-900' : 'bg-slate-700 text-slate-400'"
        >
          分镜 {{ index + 1 }} <span v-if="isExpanded">MASTER</span>
        </div>
        <div class="flex flex-col flex-1 min-w-0 mr-4">
          <!-- 标题也可以编辑 -->
          <input 
            v-if="isExpanded"
            type="text"
            :value="shot.title"
            @input="e => updateField('title', e.target.value)"
            @click.stop
            class="text-sm font-medium text-slate-200 bg-transparent border-b border-transparent hover:border-slate-600 focus:border-teal-500 focus:outline-none w-full transition-colors"
          />
          <h4 v-else class="text-sm font-medium text-slate-200 w-full truncate">{{ shot.title }}</h4>
          
          <p v-if="!isExpanded" class="text-xs text-slate-500 w-full truncate">{{ shot.visual }}</p>
        </div>
      </div>
      <div 
        class="text-slate-500 transition-transform duration-300 shrink-0" 
        :class="{'rotate-180': isExpanded}"
      >
        <ChevronDown :size="20" />
      </div>
    </div>

    <!-- 展开内容区 -->
    <div v-show="isExpanded" class="px-4 pb-6 border-t border-slate-700/50 transition-all duration-500 ease-in-out">
      <div class="grid grid-cols-12 gap-6 pt-4">
        <!-- 文本描述列 -->
        <div class="col-span-12 lg:col-span-8 space-y-5">
          <!-- Visual -->
          <div class="group">
            <div class="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase mb-1.5">
              <Image :size="12" /> 画面内容 (VISUAL)
            </div>
            <textarea
              :value="shot.visual"
              @input="e => updateField('visual', e.target.value)"
              class="w-full bg-slate-900/50 border border-slate-700/50 rounded-lg p-3 text-sm text-slate-300 leading-relaxed hover:border-slate-600 focus:border-teal-500/50 focus:ring-1 focus:ring-teal-500/50 transition-colors outline-none resize-none"
              rows="3"
            ></textarea>
          </div>

          <!-- Action -->
          <div>
            <div class="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase mb-1.5">
              <Play :size="12" /> 动作 (ACTION)
            </div>
            <textarea
              :value="shot.action"
              @input="e => updateField('action', e.target.value)"
              class="w-full bg-slate-900/50 border border-slate-700/50 rounded-lg p-3 text-sm text-slate-300 leading-relaxed hover:border-slate-600 focus:border-teal-500/50 focus:ring-1 focus:ring-teal-500/50 transition-colors outline-none resize-none"
              rows="2"
            ></textarea>
          </div>

          <!-- Camera -->
          <div>
            <div class="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase mb-1.5">
              <Video :size="12" /> 运镜 (CAMERA)
            </div>
            <textarea
              :value="shot.camera"
              @input="e => updateField('camera', e.target.value)"
              class="w-full bg-slate-900/50 border border-slate-700/50 rounded-lg p-3 text-sm text-slate-300 leading-relaxed hover:border-slate-600 focus:border-teal-500/50 focus:ring-1 focus:ring-teal-500/50 transition-colors outline-none resize-none"
              rows="2"
            ></textarea>
          </div>

          <!-- Prompt -->
          <div class="bg-slate-900 border border-blue-500/20 rounded-lg p-4 mt-2 hover:border-blue-500/40 transition-colors focus-within:border-blue-500/60 transition-all">
            <div class="flex items-center justify-between mb-2">
              <span class="text-blue-400 text-xs font-bold flex items-center gap-1">
                <Sparkles :size="12" /> 文生图提示词 (IMAGE PROMPT)
              </span>
              <button 
                @click.stop="copyPrompt"
                class="text-[10px] flex items-center gap-1 bg-slate-800 hover:bg-slate-700 px-2 py-1 rounded border border-slate-700 transition-colors"
              >
                <Check v-if="copySuccess" :size="10" class="text-green-400" />
                <Copy v-else :size="10" />
                {{ copySuccess ? '已复制' : '一键复制' }}
              </button>
            </div>
            <textarea
              :value="shot.prompt"
              @input="e => updateField('prompt', e.target.value)"
              class="w-full bg-transparent border-none p-0 text-xs text-slate-400 font-mono leading-relaxed focus:ring-0 resize-y min-h-[80px]"
            ></textarea>
          </div>

          <!-- Narration -->
          <div>
            <div class="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase mb-1.5">
              <Mic :size="12" /> 配音台词 (NARRATION)
            </div>
            <textarea
              :value="shot.narration"
              @input="e => updateField('narration', e.target.value)"
              class="w-full bg-slate-900/50 border border-slate-700/50 rounded-lg p-3 text-sm text-slate-300 leading-relaxed hover:border-slate-600 focus:border-teal-500/50 focus:ring-1 focus:ring-teal-500/50 transition-colors outline-none resize-none"
              rows="2"
              placeholder="English narration..."
            ></textarea>
          </div>

          <!-- Manifest Block (Editable) -->
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2 text-[10px] font-bold text-purple-400 uppercase">
                <FileJson :size="12" /> 视频生成 MANIFEST (VEO JSON)
              </div>
              <button 
                @click.stop="copyManifest"
                class="text-[10px] text-slate-500 hover:text-slate-300"
              >
                一键复制
              </button>
            </div>
            <textarea
              :value="shot.manifest"
              @input="e => updateField('manifest', e.target.value)"
              class="w-full bg-black/40 border border-slate-700 rounded-lg p-3 text-[10px] font-mono text-green-400 overflow-x-auto custom-scrollbar outline-none focus:border-purple-500/50 transition-colors resize-y min-h-[150px]"
            ></textarea>
          </div>

          <!-- Chinese Summary -->
          <div>
            <div class="flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase mb-1.5">
              中文大意 (CHINESE)
            </div>
            <textarea
              :value="shot.chineseSummary"
              @input="e => updateField('chineseSummary', e.target.value)"
              class="w-full bg-slate-900/30 border border-slate-700/30 rounded-lg p-3 text-xs text-slate-400 leading-relaxed hover:border-slate-600 focus:border-slate-500/50 transition-colors outline-none resize-none"
              rows="2"
            ></textarea>
          </div>
        </div>

        <!-- 右侧预览区 -->
        <div class="col-span-12 lg:col-span-4 flex flex-col gap-3">
          <div class="relative aspect-[9/16] bg-black rounded-xl overflow-hidden border border-slate-700 group shadow-lg">
            <!-- 视频播放器（当有生成的视频时显示） -->
            <template v-if="shot.generatedVideoUrl">
              <video 
                :src="shot.generatedVideoUrl"
                class="w-full h-full object-cover"
                controls
                playsinline
                loop
                @error="handleVideoError"
              >
                您的浏览器不支持视频播放
              </video>
              <!-- 视频标签 -->
              <div class="absolute top-3 left-3 bg-green-500/90 backdrop-blur-md text-white text-[10px] px-2 py-1 rounded font-bold flex items-center gap-1">
                <Film :size="10" />
                已生成视频
              </div>
            </template>
            
            <!-- 图片预览（没有视频时显示） -->
            <template v-else>
              <img :src="shot.previewUrl || shot.generatedImageUrl" alt="Preview" class="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity duration-500" />
              <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-60"></div>
            </template>
            
            <!-- 覆盖层控件（hover时显示） -->
            <div class="absolute bottom-4 left-0 right-0 px-4 flex flex-col gap-2 translate-y-2 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300">
              <!-- 生成图像按钮 -->
              <button 
                @click.stop="handleGenerateImage"
                :disabled="isGeneratingImage"
                class="bg-purple-500 hover:bg-purple-400 disabled:bg-slate-600 text-white disabled:text-slate-400 text-xs font-bold px-4 py-2 rounded-full shadow-lg flex items-center gap-2 w-full justify-center transition-colors"
              >
                <Loader2 v-if="isGeneratingImage" :size="14" class="animate-spin" />
                <Wand2 v-else :size="14" />
                {{ isGeneratingImage ? 'AI生成中...' : '生成关键帧' }}
              </button>
              <!-- 生成视频按钮 -->
              <button 
                @click.stop="handleGenerateVideo"
                :disabled="isGeneratingVideo"
                class="bg-orange-500 hover:bg-orange-400 disabled:bg-slate-600 text-white disabled:text-slate-400 text-xs font-bold px-4 py-2 rounded-full shadow-lg flex items-center gap-2 w-full justify-center transition-colors"
              >
                <Loader2 v-if="isGeneratingVideo" :size="14" class="animate-spin" />
                <Film v-else :size="14" />
                {{ isGeneratingVideo ? '视频生成中...' : (shot.generatedVideoUrl ? '重新生成视频' : '生成视频') }}
              </button>
              <!-- 重生成分镜按钮 -->
              <button 
                @click.stop="handleRegenerate"
                :disabled="isRegenerating"
                class="bg-teal-500 hover:bg-teal-400 disabled:bg-slate-600 text-slate-900 disabled:text-slate-400 text-xs font-bold px-4 py-2 rounded-full shadow-lg flex items-center gap-2 w-full justify-center transition-colors"
              >
                <Loader2 v-if="isRegenerating" :size="14" class="animate-spin" />
                <RefreshCw v-else :size="14" />
                {{ isRegenerating ? '重生成中...' : '重生成分镜' }}
              </button>
            </div>

            <div class="absolute top-3 right-3 bg-black/60 backdrop-blur-md text-white text-[10px] px-2 py-1 rounded border border-white/10">
              VEO 4K
            </div>
          </div>


        </div>
      </div>
    </div>
  </div>
</template>
