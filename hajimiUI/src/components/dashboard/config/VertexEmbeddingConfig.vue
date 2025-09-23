<script setup>
import { useDashboardStore } from '../../../stores/dashboard'
import { reactive, ref, watch } from 'vue'

const dashboardStore = useDashboardStore()

const localConfig = reactive({
  defaultModel: ''
})

const populatedFromStore = ref(false)

watch(
  () => ({
    model: dashboardStore.config.vertexEmbeddingDefaultModel,
    loaded: dashboardStore.isConfigLoaded
  }),
  (values) => {
    if (!values.loaded || populatedFromStore.value) {
      return
    }
    localConfig.defaultModel = values.model || ''
    populatedFromStore.value = true
  },
  { immediate: true, deep: true }
)

const isSaving = ref(false)

async function saveComponentConfigs(passwordFromParent) {
  if (!passwordFromParent) {
    return { success: false, message: 'Vertex Embedding 配置: 密码未提供' }
  }

  isSaving.value = true
  try {
    const trimmed = (localConfig.defaultModel || '').trim()
    if (!trimmed) {
      return { success: false, message: 'Vertex Embedding 配置: 默认模型不能为空' }
    }

    if (trimmed === (dashboardStore.config.vertexEmbeddingDefaultModel || '').trim()) {
      return { success: true, message: 'Vertex Embedding 配置: 无更改需要保存' }
    }

    await dashboardStore.updateConfig('vertexEmbeddingDefaultModel', trimmed, passwordFromParent)
    dashboardStore.config.vertexEmbeddingDefaultModel = trimmed
    return { success: true, message: 'Vertex Embedding 配置: 默认模型已更新' }
  } catch (error) {
    return {
      success: false,
      message: 'Vertex Embedding 配置: 更新失败 - ' + (error.message || '未知错误')
    }
  } finally {
    isSaving.value = false
  }
}

defineExpose({ saveComponentConfigs, localConfig })
</script>

<template>
  <div class="vertex-embedding-config">
    <h3 class="section-title">Vertex Embedding 配置</h3>

    <div class="config-form">
      <div class="config-row">
        <div class="config-group full-width">
          <label class="config-label">默认模型</label>
          <input
            type="text"
            class="config-input"
            v-model="localConfig.defaultModel"
            placeholder="例如 text-embedding-004"
          />
        </div>
      </div>

      <p class="hint-text">用于 Vertex /vertex/v1/embeddings 接口的默认模型，未在请求体中指定时会采用该值。</p>
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

.vertex-embedding-config {
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

.config-input:focus {
  outline: none;
  border-color: var(--button-primary);
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
}

.hint-text {
  margin-top: 5px;
  font-size: 13px;
  color: var(--color-muted);
  line-height: 1.5;
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
