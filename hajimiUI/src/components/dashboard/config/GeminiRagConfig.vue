<script setup>
import { useDashboardStore } from '../../../stores/dashboard'
import { reactive, ref, watch } from 'vue'

const dashboardStore = useDashboardStore()

const localConfig = reactive({
  enabled: false,
  corpus: '',
  fileIdsText: ''
})

const populatedFromStore = ref(false)

watch(
  () => ({
    enabled: dashboardStore.config.geminiRagEnabled,
    corpus: dashboardStore.config.geminiRagCorpus,
    fileIds: dashboardStore.config.geminiRagFileIds,
    loaded: dashboardStore.isConfigLoaded
  }),
  (values) => {
    if (!values.loaded || populatedFromStore.value) {
      return
    }
    localConfig.enabled = Boolean(values.enabled)
    localConfig.corpus = values.corpus || ''
    localConfig.fileIdsText = Array.isArray(values.fileIds)
      ? values.fileIds.join(',')
      : ''
    populatedFromStore.value = true
  },
  { immediate: true, deep: true }
)

const isSaving = ref(false)

async function saveComponentConfigs(passwordFromParent) {
  if (!passwordFromParent) {
    return { success: false, message: 'Gemini RAG: 密码未提供' }
  }

  let allSucceeded = true
  const messages = []
  isSaving.value = true

  const applyUpdate = async (key, value, label) => {
    try {
      await dashboardStore.updateConfig(key, value, passwordFromParent)
      messages.push()
      return true
    } catch (error) {
      messages.push()
      allSucceeded = false
      return false
    }
  }

  try {
    if (localConfig.enabled !== dashboardStore.config.geminiRagEnabled) {
      const updated = await applyUpdate('enableGeminiRag', localConfig.enabled, 'Gemini RAG 开关更新')
      if (updated) {
        dashboardStore.config.geminiRagEnabled = localConfig.enabled
      }
    }

    if (localConfig.corpus !== dashboardStore.config.geminiRagCorpus) {
      const trimmed = localConfig.corpus.trim()
      if (!trimmed) {
        allSucceeded = false
        messages.push('Gemini RAG corpus 不能为空')
      } else {
        const updated = await applyUpdate('geminiRagCorpus', trimmed, 'Gemini RAG corpus 更新')
        if (updated) {
          dashboardStore.config.geminiRagCorpus = trimmed
        }
      }
    }

    const currentFileIds = Array.isArray(dashboardStore.config.geminiRagFileIds)
      ? dashboardStore.config.geminiRagFileIds.join(',')
      : ''
    if (localConfig.fileIdsText.trim() !== currentFileIds) {
      const updated = await applyUpdate('geminiRagFileIds', localConfig.fileIdsText, 'Gemini RAG 文件 ID 更新')
      if (updated) {
        dashboardStore.config.geminiRagFileIds = localConfig.fileIdsText
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean)
      }
    }
  } finally {
    isSaving.value = false
  }

  if (messages.length === 0) {
    return {
      success: allSucceeded,
      message: allSucceeded ? 'Gemini RAG: 无更改需要保存' : 'Gemini RAG: 未保存任何更改'
    }
  }

  return {
    success: allSucceeded,
    message: 'Gemini RAG: ' + messages.join('; ')
  }
}

defineExpose({ saveComponentConfigs, localConfig })
</script>

<template>
  <div class="rag-config">
    <h3 class="section-title">Gemini RAG 配置</h3>

    <div class="config-form">
      <div class="config-row">
        <div class="config-group">
          <label class="config-label">RAG 功能</label>
          <div class="toggle-wrapper">
            <input
              type="checkbox"
              class="toggle"
              id="geminiRagEnabled"
              v-model="localConfig.enabled"
            />
            <label for="geminiRagEnabled" class="toggle-label">
              <span class="toggle-text">{{ localConfig.enabled ? '启用' : '禁用' }}</span>
            </label>
          </div>
        </div>
      </div>

      <div class="config-row">
        <div class="config-group full-width">
          <label class="config-label">Vertex RAG Corpus</label>
          <input
            type="text"
            class="config-input"
            v-model="localConfig.corpus"
            :disabled="!localConfig.enabled"
            placeholder="projects/PROJECT_ID/locations/LOCATION/ragCorpora/CORPUS_ID"
          />
        </div>
      </div>

      <div class="config-row">
        <div class="config-group full-width">
          <label class="config-label">RAG 文件 ID（可选，逗号分隔）</label>
          <input
            type="text"
            class="config-input"
            v-model="localConfig.fileIdsText"
            :disabled="!localConfig.enabled"
            placeholder="fileA,fileB,fileC"
          />
        </div>
      </div>

      <p class="hint-text">使用 Vertex RAG Store 数据源，启用后会注入检索工具，并刷新模型列表以显示带 <code>-rag</code> 后缀的模型。</p>
      <div class="save-indicator" v-if="isSaving">保存中...</div>
    </div>
  </div>
</template>

<style scoped>
.section-title {
  color: var(--color-heading);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 10px;
  margin-bottom: 20px;
  position: relative;
  font-weight: 600;
}

.section-title::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 50px;
  height: 2px;
  background: var(--gradient-primary);
}

.rag-config {
  margin-bottom: 25px;
}

.config-form {
  background-color: var(--stats-item-bg);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--card-border);
}

.config-row {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.config-group {
  flex: 1;
  min-width: 160px;
}

.full-width {
  flex-basis: 100%;
}

.config-label {
  display: block;
  font-size: 14px;
  margin-bottom: 5px;
  color: var(--color-text);
  font-weight: 500;
}

.config-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-background);
  color: var(--color-text);
  font-size: 14px;
  transition: all 0.3s ease;
}

.config-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.config-input:focus {
  outline: none;
  border-color: var(--button-primary);
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
}

.toggle-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.toggle {
  width: 48px;
  height: 24px;
  position: relative;
  appearance: none;
  background-color: var(--color-border);
  border-radius: 999px;
  transition: background-color 0.3s ease;
  cursor: pointer;
}

.toggle:checked {
  background-color: var(--button-primary);
}

.toggle::before {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background-color: #fff;
  border-radius: 50%;
  transition: transform 0.3s ease;
}

.toggle:checked::before {
  transform: translateX(24px);
}

.toggle-label {
  cursor: pointer;
  user-select: none;
}

.toggle-text {
  font-size: 14px;
  color: var(--color-text);
}

.hint-text {
  margin-top: 5px;
  font-size: 13px;
  color: var(--color-muted);
  line-height: 1.5;
}

.hint-text code {
  background: rgba(0, 0, 0, 0.05);
  padding: 0 4px;
  border-radius: 4px;
}

.save-indicator {
  margin-top: 10px;
  font-size: 13px;
  color: var(--color-muted);
}

@media (max-width: 480px) {
  .config-row {
    flex-direction: column;
  }
}
</style>
