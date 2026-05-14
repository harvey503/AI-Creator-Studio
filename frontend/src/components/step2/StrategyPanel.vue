<script setup>
import { useStoryboardStore } from '../../stores/storyboard'
import { Sparkles, CheckCircle } from 'lucide-vue-next'

const storyboardStore = useStoryboardStore()
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center gap-2 mb-4">
      <div class="p-1.5 bg-teal-500/10 rounded-lg text-teal-400">
        <Sparkles :size="18" />
      </div>
      <h3 class="font-bold text-slate-100">专家团队分析报告</h3>
    </div>

    <!-- 合规性检查 -->
    <div class="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 transition-all hover:bg-slate-800/70">
      <div class="flex items-center gap-2 text-teal-400 text-xs font-bold mb-2">
        <CheckCircle :size="14" /> TIKTOK 合规性 & 文化检查
      </div>
      <div class="flex items-center gap-2 mb-2">
        <span class="text-xs text-slate-400">风险等级 (Risk Level)</span>
        <span 
          class="text-[10px] px-2 py-0.5 rounded font-bold border"
          :class="storyboardStore.strategyReport.riskLevel === 'safe' 
            ? 'bg-green-500/20 text-green-400 border-green-500/30' 
            : 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'"
        >
          {{ storyboardStore.strategyReport.riskLevel === 'safe' ? 'Safe' : 'Warning' }}
        </span>
      </div>
      <p class="text-xs text-slate-400 leading-relaxed">
        脚本内容符合TikTok广告政策。未涉及夸大功效或品牌名称侵权。使用了 "hydrating" (保湿) 和 "shine" (光泽) 等合规词汇。
      </p>
    </div>

    <!-- 文化备注 -->
    <div class="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 transition-all hover:bg-slate-800/70">
      <div class="text-slate-300 text-xs font-bold mb-2">文化背景备注 (CULTURE NOTES)</div>
      <p class="text-xs text-slate-400 leading-relaxed italic border-l-2 border-slate-600 pl-2">
        "{{ storyboardStore.strategyReport.cultureNotes }}"
      </p>
    </div>

    <!-- 核心策略 -->
    <div class="bg-gradient-to-br from-slate-800 to-slate-800/50 border border-purple-500/30 rounded-xl p-4 relative overflow-hidden group">
      <div class="absolute top-0 right-0 w-16 h-16 bg-purple-500/10 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110 duration-500"></div>
      <div class="text-purple-300 text-xs font-bold mb-2 flex items-center gap-2">
        <div class="w-1.5 h-1.5 bg-purple-400 rounded-full animate-pulse"></div>
        核心策略 (CORE STRATEGY)
      </div>
      <p class="text-xs text-slate-300 leading-relaxed">
        {{ storyboardStore.strategyReport.coreStrategy }}
      </p>
    </div>

    <!-- 钩子 -->
    <div class="bg-slate-800 border border-slate-700 rounded-xl p-4 shadow-sm">
      <div class="text-slate-400 text-[10px] font-bold uppercase mb-1">强钩子 (HOOK)</div>
      <p class="text-sm font-medium text-white">
        "{{ storyboardStore.strategyReport.hook }}"
      </p>
    </div>
  </div>
</template>
