import { createRouter, createWebHistory } from 'vue-router'
import Step1View from '../views/Step1View.vue'
import Step2View from '../views/Step2View.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'step1',
            component: Step1View
        },
        {
            path: '/generate',
            name: 'step2',
            component: Step2View
        }
    ]
})

export default router
