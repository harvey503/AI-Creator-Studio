import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
    uploadProductImages,
    uploadModelImages,
    uploadReferenceVideo,
    deleteUploadedFile
} from '../api/client'

export const useProjectStore = defineStore('project', () => {
    // 项目配置
    const config = ref({
        market: 'US',
        productName: '',
        productDesc: '',
        creativeIdea: '逐帧复刻，更强的钩子。需要换一个模特、换一个场景。',
        aspectRatio: '9:16',
        resolution: '2K',
        generationMode: 'first_frame',
        shotCount: 2
    })

    // 素材资源
    const assets = ref({
        productImages: [],  // [{url, filename, original_name}]
        modelImages: [],    // [{url, filename, original_name}]
        referenceVideo: null // {url, filename, original_name}
    })

    // 更新配置
    function updateConfig(key, value) {
        config.value[key] = value
    }

    // 上传产品图片
    async function uploadProduct(files) {
        const response = await uploadProductImages(files)
        return response
    }

    // 上传模特图片
    async function uploadModel(files) {
        const response = await uploadModelImages(files)
        return response
    }

    // 上传参考视频
    async function uploadReference(file) {
        const response = await uploadReferenceVideo(file)
        assets.value.referenceVideo = {
            url: response.url,
            filename: response.filename,
            original_name: response.original_name
        }
        return response
    }

    // 删除产品图片
    async function deleteProductImage(filename) {
        await deleteUploadedFile('product', filename)
    }

    // 删除模特图片
    async function deleteModelImage(filename) {
        await deleteUploadedFile('model', filename)
    }

    // 删除参考视频
    async function deleteReference() {
        if (assets.value.referenceVideo?.filename) {
            await deleteUploadedFile('reference', assets.value.referenceVideo.filename)
            assets.value.referenceVideo = null
        }
    }

    // 设置产品图片列表
    function setProductImages(images) {
        assets.value.productImages = images
    }

    // 设置模特图片列表
    function setModelImages(images) {
        assets.value.modelImages = images
    }

    return {
        config,
        assets,
        updateConfig,
        uploadProduct,
        uploadModel,
        uploadReference,
        deleteProductImage,
        deleteModelImage,
        deleteReference,
        setProductImages,
        setModelImages
    }
}, {
    persist: true
})
