/**
 * API客户端
 * 用于与后端API通信
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * 发送API请求
 */
async function request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`

    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    }

    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    }

    try {
        const response = await fetch(url, mergedOptions)

        if (!response.ok) {
            const error = await response.json().catch(() => ({}))
            throw new Error(error.detail || `HTTP error! status: ${response.status}`)
        }

        return await response.json()
    } catch (error) {
        console.error('API request failed:', error)
        throw error
    }
}

/**
 * 策略分析API
 */
export async function analyzeStrategy(data) {
    return request('/api/v1/analyze/strategy', {
        method: 'POST',
        body: JSON.stringify(data),
    })
}

/**
 * 生成分镜脚本API
 */
export async function generateStoryboard(data) {
    return request('/api/v1/generate/storyboard', {
        method: 'POST',
        body: JSON.stringify(data),
    })
}

/**
 * 重生成单个分镜API
 */
export async function regenerateShot(data) {
    return request('/api/v1/generate/shot/regenerate', {
        method: 'POST',
        body: JSON.stringify(data),
    })
}

/**
 * 快速生成第一个分镜（开场镜头）
 * 优化响应时间，只生成一个分镜
 */
export async function generateFirstShot(data) {
    return request('/api/v1/generate/storyboard/first', {
        method: 'POST',
        body: JSON.stringify(data),
    })
}

/**
 * 基于第一个分镜生成剩余分镜
 */
export async function generateRemainingShots(data) {
    return request('/api/v1/generate/storyboard/remaining', {
        method: 'POST',
        body: JSON.stringify(data),
    })
}

/**
 * 健康检查API
 */
export async function healthCheck() {
    return request('/api/v1/health')
}

// ==================== 文件上传API ====================

/**
 * 上传产品图片
 * @param {FileList|File[]} files - 文件列表（最多5张）
 * @returns {Promise<{files: Array, count: number}>}
 */
export async function uploadProductImages(files) {
    const formData = new FormData()
    for (const file of files) {
        formData.append('files', file)
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/upload/product`, {
        method: 'POST',
        body: formData,
    })

    if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        throw new Error(error.detail || `上传失败: ${response.status}`)
    }

    return await response.json()
}

/**
 * 上传模特图片
 * @param {FileList|File[]} files - 文件列表（最多3张）
 * @returns {Promise<{files: Array, count: number}>}
 */
export async function uploadModelImages(files) {
    const formData = new FormData()
    for (const file of files) {
        formData.append('files', file)
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/upload/model`, {
        method: 'POST',
        body: formData,
    })

    if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        throw new Error(error.detail || `上传失败: ${response.status}`)
    }

    return await response.json()
}

/**
 * 上传参考视频
 * @param {File} file - 视频文件
 * @returns {Promise<Object>}
 */
export async function uploadReferenceVideo(file) {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE_URL}/api/v1/upload/reference`, {
        method: 'POST',
        body: formData,
    })

    if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        throw new Error(error.detail || `上传失败: ${response.status}`)
    }

    return await response.json()
}

/**
 * 删除上传的文件
 * @param {string} category - 文件分类
 * @param {string} filename - 文件名
 * @returns {Promise<Object>}
 */
export async function deleteUploadedFile(category, filename) {
    return request(`/api/v1/upload/files/${category}/${filename}`, {
        method: 'DELETE',
    })
}

/**
 * 获取上传文件的完整URL
 * @param {string} url - 相对URL
 * @returns {string} 完整URL
 */
export function getUploadUrl(url) {
    if (!url) return ''
    if (url.startsWith('http')) return url
    return `${API_BASE_URL}${url}`
}

// ==================== 图像生成API ====================

/**
 * 生成单张图像
 * @param {Object} data - {prompt, aspect_ratio, model}
 * @returns {Promise<{url, local_path, prompt, model, status}>}
 */
export async function generateImage(data) {
    return request('/api/v1/image/generate', {
        method: 'POST',
        body: JSON.stringify(data),
    })
}

/**
 * 批量生成图像
 * @param {Object} data - {prompts: string[], aspect_ratio, model}
 * @returns {Promise<{results: Array, total, success_count}>}
 */
export async function generateImageBatch(data) {
    return request('/api/v1/image/generate/batch', {
        method: 'POST',
        body: JSON.stringify(data),
    })
}

/**
 * 为分镜生成关键帧图像
 * @param {Object} data - {shot_id, prompt, aspect_ratio, model}
 * @returns {Promise<{url, prompt, status}>}
 */
export async function generateShotImage(data) {
    return request('/api/v1/image/generate/shot', {
        method: 'POST',
        body: JSON.stringify(data),
    })
}

/**
 * 获取可用的图像生成模型列表
 * @returns {Promise<{models: Array}>}
 */
export async function getImageModels() {
    return request('/api/v1/image/models')
}

// ==================== 视频生成API ====================

/**
 * 生成视频
 * @param {Object} data - {image_url, prompt, duration, provider, aspect_ratio}
 * @returns {Promise<{video_url, duration, status, task_id}>}
 */
export async function generateVideo(data) {
    return request('/api/v1/video/generate', {
        method: 'POST',
        body: JSON.stringify(data),
    })
}

/**
 * 为分镜生成视频片段
 * @param {Object} data - {shot_id, image_url, prompt, duration, provider, aspect_ratio}
 * @returns {Promise<{video_url, duration, status}>}
 */
export async function generateShotVideo(data) {
    return request('/api/v1/video/generate/shot', {
        method: 'POST',
        body: JSON.stringify(data),
    })
}

/**
 * 查询视频生成任务状态
 * @param {Object} data - {task_id, provider}
 * @returns {Promise<{task_id, status, progress, video_url}>}
 */
export async function getVideoTaskStatus(data) {
    return request('/api/v1/video/status', {
        method: 'POST',
        body: JSON.stringify(data),
    })
}

/**
 * 合并多个视频
 * @param {Object} data - {video_urls: string[], output_filename: string}
 * @returns {Promise<{video_url, local_path, duration, status}>}
 */
export async function mergeVideos(data) {
    return request('/api/v1/video/merge', {
        method: 'POST',
        body: JSON.stringify(data),
    })
}

/**
 * 获取可用的视频生成提供商列表
 * @returns {Promise<{providers: Array}>}
 */
export async function getVideoProviders() {
    return request('/api/v1/video/providers')
}

export default {
    analyzeStrategy,
    generateStoryboard,
    regenerateShot,
    generateFirstShot,
    generateRemainingShots,
    healthCheck,
    uploadProductImages,
    uploadModelImages,
    uploadReferenceVideo,
    deleteUploadedFile,
    getUploadUrl,
    generateImage,
    generateImageBatch,
    generateShotImage,
    getImageModels,
    generateVideo,
    generateShotVideo,
    getVideoTaskStatus,
    getVideoProviders,
    mergeVideos,
}


