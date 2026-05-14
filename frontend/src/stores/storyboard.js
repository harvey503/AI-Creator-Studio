import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useProjectStore } from './project'
import { generateStoryboard, regenerateShot, generateShotImage, generateShotVideo, generateFirstShot, generateRemainingShots, mergeVideos } from '../api/client'

export const useStoryboardStore = defineStore('storyboard', () => {
    // 加载状态
    const isLoading = ref(false)
    const error = ref(null)

    // 分步加载状态
    const isGeneratingFirst = ref(false)  // 正在生成第一个分镜
    const isGeneratingRemaining = ref(false)  // 正在生成剩余分镜
    const hasFirstShot = ref(false)  // 是否已生成第一个分镜
    const isRegenerating = ref(false) // 是否正在重生成分镜

    // 视频合并状态
    const isMerging = ref(false)
    const mergedVideoUrl = ref(null)

    // 图像生成状态 {shotId: 'generating' | 'completed' | 'failed'}
    const imageGeneratingStatus = ref({})

    // 视频生成状态 {shotId: 'generating' | 'completed' | 'failed'}
    const videoGeneratingStatus = ref({})

    // 策略分析报告
    const strategyReport = ref({
        riskLevel: 'safe',
        cultureNotes: '',
        coreStrategy: '',
        hook: ''
    })

    // 分镜列表
    const shots = ref([])

    // 当前展开的分镜索引
    const expandedIndex = ref(0)

    // 切换分镜展开状态
    function toggleShot(index) {
        expandedIndex.value = expandedIndex.value === index ? -1 : index
    }

    // 更新分镜内容
    function updateShot(index, field, value) {
        shots.value[index][field] = value
    }

    // 生成VEO Manifest JSON
    function generateManifest(shot, aspectRatio = '9:16') {
        let summary = shot.videoPrompt || shot.prompt || '';
        if (shot.narration) {
            summary += `. Narration: "${shot.narration}"`;
        }

        return {
            veo_production_manifest: {
                version: '4.0',
                shot_summary: summary,
                description: "Cinematic commercial video.",
                global_settings: {
                    input_assets: {
                        reference_image: "Start Frame"
                    },
                    output_specifications: {
                        resolution: "1080p",
                        aspect_ratio_lock: {
                            enabled: true
                        },
                        parameters: {
                            aspectRatio: aspectRatio
                        }
                    },
                    color_space: "Rec. 2020",
                    dynamic_range: "HDR"
                }
            }
        }
    }

    // 调用后端API生成分镜脚本
    async function generate(projectConfig) {
        isLoading.value = true
        error.value = null

        try {
            const response = await generateStoryboard({
                market: projectConfig.market,
                product_name: projectConfig.productName,
                product_desc: projectConfig.productDesc,
                creative_idea: projectConfig.creativeIdea,
                aspect_ratio: projectConfig.aspectRatio,
                resolution: projectConfig.resolution
            })

            // 更新策略报告
            strategyReport.value = {
                riskLevel: response.strategy_report.risk_level,
                cultureNotes: response.strategy_report.culture_notes,
                coreStrategy: response.strategy_report.core_strategy,
                hook: response.strategy_report.hook
            }

            // 更新分镜列表
            shots.value = response.shots.map(shot => {
                const s = {
                    id: shot.id,
                    title: shot.title,
                    visual: shot.visual,
                    action: shot.action,
                    camera: shot.camera,
                    prompt: shot.prompt,
                    chineseSummary: shot.chinese_summary,
                    narration: shot.narration,
                    videoPrompt: shot.video_prompt,
                    previewUrl: shot.preview_url,
                    generatedImageUrl: null
                }
                s.manifest = JSON.stringify(generateManifest(s, projectConfig.aspectRatio), null, 2)
                return s
            })

            // 默认展开第一个分镜
            expandedIndex.value = 0

            return response
        } catch (err) {
            error.value = err.message
            console.error('Failed to generate storyboard:', err)
            throw err
        } finally {
            isLoading.value = false
        }
    }

    // 重新生成单个分镜
    async function regenerate(shotId, modificationHint = '') {
        const shotIndex = shots.value.findIndex(s => s.id === shotId)
        if (shotIndex === -1) return

        isRegenerating.value = true
        error.value = null

        try {
            const configStore = useProjectStore()
            const config = configStore.config
            const firstShot = shots.value[0]

            console.log('[Regenerate] Starting with context:', {
                shotId,
                productName: config.productName,
                hasFirstShot: !!firstShot,
                modificationHint
            })

            const payload = {
                shot_id: shotId,
                current_prompt: shots.value[shotIndex].prompt,
                modification_hint: modificationHint,
                product_name: config.productName,
                product_desc: config.productDesc,
                first_shot: firstShot ? {
                    id: firstShot.id,
                    title: firstShot.title,
                    visual: firstShot.visual,
                    action: firstShot.action,
                    camera: firstShot.camera,
                    prompt: firstShot.prompt,
                    chinese_summary: firstShot.chineseSummary
                } : null
            }

            console.log('[Regenerate] API Payload Sent:', payload)

            const response = await regenerateShot(payload)

            const newShot = {
                id: response.id,
                title: response.title,
                visual: response.visual,
                action: response.action,
                camera: response.camera,
                prompt: response.prompt,
                chineseSummary: response.chinese_summary,
                narration: response.narration,
                videoPrompt: response.video_prompt,
                previewUrl: response.preview_url,
                generatedImageUrl: null
            }
            newShot.manifest = JSON.stringify(generateManifest(newShot, config.aspectRatio), null, 2)
            shots.value[shotIndex] = newShot

            return response
        } catch (err) {
            error.value = err.message
            console.error('Failed to regenerate shot:', err)
            throw err
        } finally {
            isRegenerating.value = false
        }
    }

    // ============ 分步生成方法 ============

    /**
     * 快速生成第一个分镜（开场镜头）
     * 优化响应时间，预计5-8秒
     */
    async function generateFirstShotOnly(projectConfig) {
        isGeneratingFirst.value = true
        error.value = null
        hasFirstShot.value = false

        try {
            const response = await generateFirstShot({
                market: projectConfig.market,
                product_name: projectConfig.productName,
                product_desc: projectConfig.productDesc,
                creative_idea: projectConfig.creativeIdea,
                aspect_ratio: projectConfig.aspectRatio,
                resolution: projectConfig.resolution
            })

            // 设置第一个分镜
            const shot = response.shot
            const firstShotObj = {
                id: shot.id,
                title: shot.title,
                visual: shot.visual,
                action: shot.action,
                camera: shot.camera,
                prompt: shot.prompt,
                chineseSummary: shot.chinese_summary,
                narration: shot.narration,
                videoPrompt: shot.video_prompt,
                previewUrl: shot.preview_url,
                generatedImageUrl: null
            }
            firstShotObj.manifest = JSON.stringify(generateManifest(firstShotObj, projectConfig.aspectRatio), null, 2)
            shots.value = [firstShotObj]

            // 设置默认的空策略报告（跳过策略报告生成）
            strategyReport.value = {
                riskLevel: 'safe',
                cultureNotes: '',
                coreStrategy: '',
                hook: ''
            }

            expandedIndex.value = 0
            hasFirstShot.value = true

            // 自动开始生成第一张关键帧（不等待，后台执行）
            generateImageForShot(shot.id, projectConfig.aspectRatio)

            return response
        } catch (err) {
            error.value = err.message
            console.error('Failed to generate first shot:', err)
            throw err
        } finally {
            isGeneratingFirst.value = false
        }
    }

    /**
     * 基于第一个分镜生成剩余分镜
     */
    async function generateRemaining(projectConfig) {
        if (shots.value.length === 0) {
            throw new Error('请先生成第一个分镜')
        }

        isGeneratingRemaining.value = true
        error.value = null

        try {
            // 获取第一个分镜数据
            const firstShot = shots.value[0]

            const payload = {
                market: projectConfig.market,
                product_name: projectConfig.productName,
                product_desc: projectConfig.productDesc,
                creative_idea: projectConfig.creativeIdea,
                aspect_ratio: projectConfig.aspectRatio,
                resolution: projectConfig.resolution,
                first_shot: {
                    id: firstShot.id,
                    title: firstShot.title,
                    visual: firstShot.visual,
                    action: firstShot.action,
                    camera: firstShot.camera,
                    prompt: firstShot.prompt,
                    chinese_summary: firstShot.chineseSummary,
                    preview_url: firstShot.previewUrl
                },
                first_shot_image_url: firstShot.generatedImageUrl || firstShot.previewUrl,
                shot_count: projectConfig.shotCount || 5
            }
            const response = await generateRemainingShots(payload)

            // 添加剩余分镜到列表
            const remainingShots = response.shots.map(shot => {
                const s = {
                    id: shot.id,
                    title: shot.title,
                    visual: shot.visual,
                    action: shot.action,
                    camera: shot.camera,
                    prompt: shot.prompt,
                    chineseSummary: shot.chinese_summary,
                    narration: shot.narration,
                    videoPrompt: shot.video_prompt,
                    previewUrl: shot.preview_url,
                    generatedImageUrl: null
                }
                s.manifest = JSON.stringify(generateManifest(s, projectConfig.aspectRatio), null, 2)
                return s
            })

            shots.value = [...shots.value, ...remainingShots]
            console.log('Debug AutoGen:', {
                autoGenerate: projectConfig.autoGenerateImage,
                shotsLength: remainingShots.length,
                fullConfig: projectConfig
            })

            // 自动开始生成剩余分镜的关键帧
            if (projectConfig.autoGenerateImage !== false) {
                // 获取第一张分镜图片作为参考
                const firstShotImage = shots.value[0]?.generatedImageUrl || shots.value[0]?.previewUrl

                remainingShots.forEach(shot => {
                    generateImageForShot(shot.id, projectConfig.aspectRatio, firstShotImage)
                })
            }

            return response
        } catch (err) {
            error.value = err.message
            console.error('Failed to generate remaining shots:', err)
            throw err
        } finally {
            isGeneratingRemaining.value = false
        }
    }

    /**
     * 合并所有分镜视频
     */
    async function mergeAllVideos() {
        // 1. 收集所有已生成的视频URL
        const videoUrls = shots.value
            .filter(shot => shot.generatedVideoUrl)
            .map(shot => shot.generatedVideoUrl)

        if (videoUrls.length === 0) {
            throw new Error('没有可合并的视频片段，请先生成分镜视频')
        }

        if (videoUrls.length < shots.value.length) {
            console.warn('部分分镜尚未生成视频，仅合并已完成的部分')
        }

        isMerging.value = true
        error.value = null
        mergedVideoUrl.value = null

        try {
            const config = useProjectStore().config
            const response = await mergeVideos({
                video_urls: videoUrls,
                aspect_ratio: config.aspectRatio || '9:16',
                resolution: config.resolution || '1080p',
                output_filename: `project_merged_${Date.now()}.mp4`
            })

            mergedVideoUrl.value = response.video_url
            return response
        } catch (err) {
            error.value = err.message
            console.error('Failed to merge videos:', err)
            throw err
        } finally {
            isMerging.value = false
        }
    }


    // 为分镜生成关键帧图像 - 后端默认使用nano-banana
    async function generateImageForShot(shotId, aspectRatio = '9:16', referenceImageUrl = null) {
        const shotIndex = shots.value.findIndex(s => s.id === shotId)
        if (shotIndex === -1) return

        const shot = shots.value[shotIndex]
        imageGeneratingStatus.value[shotId] = 'generating'

        try {
            const projectStore = useProjectStore()
            const config = projectStore.config

            if (!referenceImageUrl && projectStore.assets.productImages?.length > 0) {
                referenceImageUrl = projectStore.assets.productImages[0].url
                console.log('[ImageGen] Using product image as reference:', referenceImageUrl)
            }

            const payload = {
                shot_id: shotId,
                prompt: shot.prompt,
                aspect_ratio: config.aspectRatio || aspectRatio,
                resolution: config.resolution || '1080p'
                // model参数不传递，由后端配置决定使用哪个模型
            }

            if (referenceImageUrl) {
                payload.reference_image_url = referenceImageUrl
            }

            const response = await generateShotImage(payload)

            shots.value[shotIndex].generatedImageUrl = response.url
            shots.value[shotIndex].previewUrl = response.url
            imageGeneratingStatus.value[shotId] = 'completed'

            return response
        } catch (err) {
            imageGeneratingStatus.value[shotId] = 'failed'
            console.error('Failed to generate image for shot:', err)
            throw err
        }
    }

    // 检查某个分镜是否正在生成图像
    function isGeneratingImage(shotId) {
        return imageGeneratingStatus.value[shotId] === 'generating'
    }

    // 为分镜生成视频 - 后端默认使用VEO
    async function generateVideoForShot(shotId, duration = 5) {
        const shotIndex = shots.value.findIndex(s => s.id === shotId)
        if (shotIndex === -1) return

        const shot = shots.value[shotIndex]

        // 需要先有生成的关键帧图像
        const imageUrl = shot.generatedImageUrl || shot.previewUrl
        if (!imageUrl) {
            throw new Error('请先生成关键帧图像')
        }

        videoGeneratingStatus.value[shotId] = 'generating'

        try {
            const config = useProjectStore().config
            const response = await generateShotVideo({
                shot_id: shotId,
                image_url: imageUrl,
                prompt: shot.action || shot.prompt,
                duration: duration,
                aspect_ratio: config.aspectRatio || '9:16',
                resolution: config.resolution || '1080p',
                veo_manifest: shot.manifest ? JSON.parse(shot.manifest) : null
                // provider参数不传递，由后端配置决定使用哪个提供商
            })

            shots.value[shotIndex].generatedVideoUrl = response.video_url
            videoGeneratingStatus.value[shotId] = 'completed'

            return response
        } catch (err) {
            videoGeneratingStatus.value[shotId] = 'failed'
            console.error('Failed to generate video for shot:', err)
            throw err
        }
    }

    // 检查某个分镜是否正在生成视频
    function isGeneratingVideo(shotId) {
        return videoGeneratingStatus.value[shotId] === 'generating'
    }

    // 设置初始mock数据
    function setMockData() {
        strategyReport.value = {
            riskLevel: 'safe',
            cultureNotes: '使用了美国 "Clean Girl Aesthetic" 风格，强调自然妆容和保湿效果。',
            coreStrategy: '利用"讲解+展示"形式，结合色号展示选中诱惑感。',
            hook: '这不是普通的口红，这是固体唇油！'
        }

        shots.value = [
            {
                id: 1,
                title: '高清特写，展示产品第一印象',
                visual: '中景镜头。一位年轻漂亮的女性，妆容自然精致。',
                action: '模特展示产品，眼睛瞪大表示惊喜。',
                camera: '固定镜头，焦点在模特面部和产品。',
                prompt: 'Medium shot of a beautiful young woman with natural makeup, holding lipstick, looking surprised. High quality, 4k.',
                chineseSummary: '你看到这个了吗？太不可思议了！',
                previewUrl: 'https://images.unsplash.com/photo-1515934751635-c81c6bc9a2d8?auto=format&fit=crop&q=80&w=600',
                generatedImageUrl: null
            },
            {
                id: 2,
                title: '手部特写，展示产品质感',
                visual: '模特展示产品的高级质感和设计细节。',
                action: 'Focus on hands holding the product.',
                camera: '微距镜头，浅景深。',
                prompt: 'Close up of hands holding lipstick, elegant design, cinematic lighting.',
                chineseSummary: '质感完全不输大牌！',
                previewUrl: 'https://images.unsplash.com/photo-1522337660859-02fbefca4702?auto=format&fit=crop&q=80&w=600',
                generatedImageUrl: null
            },
            {
                id: 3,
                title: '使用过程特写',
                visual: '展示产品的实际使用效果。',
                action: 'Application demonstration.',
                camera: 'Macro close-up.',
                prompt: 'Macro shot of lipstick application, high gloss texture, 8k resolution.',
                chineseSummary: '效果太惊艳了！',
                previewUrl: 'https://images.unsplash.com/photo-1596462502278-27bfdd403348?auto=format&fit=crop&q=80&w=600',
                generatedImageUrl: null
            },
            {
                id: 4,
                title: '最终效果展示',
                visual: '模特自信微笑，展示完美效果。',
                action: 'Model smiling confidently.',
                camera: 'Portrait shot, soft lighting.',
                prompt: 'Portrait of girl with glossy lips, smiling, studio lighting, beauty commercial style.',
                chineseSummary: '看看这个效果，太完美了！',
                previewUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=600',
                generatedImageUrl: null
            }
        ]

        // Add mock narration and manifest
        shots.value = shots.value.map(s => {
            s.narration = "Default mock narration text."
            s.videoPrompt = "Default mock video prompt description."
            s.manifest = JSON.stringify(generateManifest(s, '9:16'), null, 2)
            return s
        })
    }

    // 获取上传文件的完整URL
    function getUploadUrl(path) {
        if (!path) return ''
        if (path.startsWith('http')) return path
        // 移除开头的/api/v1前缀（如果存在），因为后端返回的可能是/api/v1/upload/...
        // 但这里我们简单处理，直接使用VITE_API_BASE_URL拼接
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

        // 确保path以/开头
        const cleanPath = path.startsWith('/') ? path : `/${path}`

        // 如果baseUrl以/结尾，去掉它
        const cleanBaseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl

        return `${cleanBaseUrl}${cleanPath}`
    }

    return {
        isLoading,
        error,
        isGeneratingFirst,
        isGeneratingRemaining,
        hasFirstShot,
        isRegenerating,
        isMerging,
        mergedVideoUrl,
        imageGeneratingStatus,
        videoGeneratingStatus,
        strategyReport,
        shots,
        expandedIndex,
        toggleShot,
        updateShot,
        generateManifest,
        generate,
        regenerate,
        generateFirstShotOnly,
        generateRemaining,
        mergeAllVideos,
        generateImageForShot,
        isGeneratingImage,
        generateVideoForShot,
        isGeneratingVideo,
        setMockData,
        getUploadUrl
    }
})
