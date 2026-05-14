<script setup>
import { ref, computed } from 'vue'
import { Upload, X, Loader2, Image, AlertCircle } from 'lucide-vue-next'
import { getUploadUrl } from '../../api/client'

const props = defineProps({
  // 已上传的文件列表 [{url, filename, original_name}]
  modelValue: {
    type: Array,
    default: () => []
  },
  // 最大文件数量
  maxFiles: {
    type: Number,
    default: 5
  },
  // 接受的文件类型
  accept: {
    type: String,
    default: 'image/*'
  },
  // 上传函数
  uploadFn: {
    type: Function,
    required: true
  },
  // 删除函数
  deleteFn: {
    type: Function,
    default: null
  },
  // 占位符数量
  placeholders: {
    type: Number,
    default: 4
  }
})

const emit = defineEmits(['update:modelValue', 'error'])

const isUploading = ref(false)
const errorMessage = ref('')

const files = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const remainingSlots = computed(() => {
  return Math.max(0, props.maxFiles - files.value.length)
})

const placeholderCount = computed(() => {
  return Math.min(props.placeholders, remainingSlots.value)
})

const handleFileSelect = async (event) => {
  const selectedFiles = Array.from(event.target.files)
  if (!selectedFiles.length) return

  // 检查数量限制
  if (selectedFiles.length > remainingSlots.value) {
    errorMessage.value = `最多只能上传${props.maxFiles}个文件`
    return
  }

  errorMessage.value = ''
  isUploading.value = true

  try {
    const response = await props.uploadFn(selectedFiles)
    
    // 添加到文件列表
    const newFiles = response.files.map(f => ({
      url: f.url,
      filename: f.filename,
      original_name: f.original_name,
      size: f.size
    }))
    
    files.value = [...files.value, ...newFiles]
  } catch (error) {
    errorMessage.value = error.message || '上传失败'
    emit('error', error)
  } finally {
    isUploading.value = false
    // 清空input以便重复选择同一文件
    event.target.value = ''
  }
}

const removeFile = async (index) => {
  const file = files.value[index]
  
  // 如果有删除函数，调用删除API
  if (props.deleteFn && file.filename) {
    try {
      await props.deleteFn(file.filename)
    } catch (error) {
      console.error('删除文件失败:', error)
    }
  }
  
  // 从列表中移除
  const newFiles = [...files.value]
  newFiles.splice(index, 1)
  files.value = newFiles
}

const getFullUrl = (url) => {
  return getUploadUrl(url)
}
</script>

<template>
  <div class="space-y-2">
    <!-- 错误提示 -->
    <div v-if="errorMessage" class="flex items-center gap-2 text-red-400 text-xs">
      <AlertCircle :size="14" />
      {{ errorMessage }}
    </div>

    <!-- 文件网格 -->
    <div class="grid gap-3" :class="`grid-cols-${Math.min(5, maxFiles)}`">
      <!-- 已上传的文件 -->
      <div 
        v-for="(file, index) in files" 
        :key="file.filename || index"
        class="aspect-square bg-slate-800 rounded-lg border border-teal-500/50 relative overflow-hidden group cursor-pointer shadow-lg shadow-teal-900/10"
      >
        <img 
          :src="getFullUrl(file.url)" 
          :alt="file.original_name" 
          class="w-full h-full object-cover"
        />
        <!-- 删除按钮 -->
        <button 
          @click="removeFile(index)"
          class="absolute top-1 right-1 bg-red-500 hover:bg-red-400 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <X :size="12" />
        </button>
        <!-- 文件名提示 -->
        <div class="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-[10px] px-2 py-1 truncate opacity-0 group-hover:opacity-100 transition-opacity">
          {{ file.original_name }}
        </div>
      </div>

      <!-- 上传按钮 -->
      <label 
        v-for="i in placeholderCount" 
        :key="`placeholder-${i}`"
        class="aspect-square bg-slate-800/50 rounded-lg border border-slate-700 border-dashed flex items-center justify-center text-slate-600 hover:text-slate-400 hover:border-slate-500 cursor-pointer transition-colors duration-200"
        :class="{ 'pointer-events-none opacity-50': isUploading }"
      >
        <input 
          type="file" 
          :accept="accept"
          :multiple="remainingSlots > 1"
          @change="handleFileSelect"
          class="hidden"
          :disabled="isUploading"
        />
        <Loader2 v-if="isUploading && i === 1" :size="18" class="animate-spin" />
        <Upload v-else :size="18" />
      </label>
    </div>
  </div>
</template>

<style scoped>
.grid-cols-3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
.grid-cols-4 {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}
.grid-cols-5 {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}
</style>
