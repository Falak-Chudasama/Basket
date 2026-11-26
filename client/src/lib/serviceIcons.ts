import type { ServiceStatus } from '../types/api'

const SERVICE_ICON_MAP: Record<string, string> = {
  'basket-control': '/icons/basket-icon.svg',
  'basket-api': '/icons/basket-icon.svg',
  nginx: '/icons/nginx-icon.svg',
  mongodb: '/icons/mongodb-icon.svg',
  'llm-llama': '/icons/llm-icon.svg',
  'tts-pocket': '/icons/tts-icon.svg',
  'stt-qwen': '/icons/stt-icon.svg',
  'fruit-banana': '/icons/banana-icon.svg',
  'fruit-kiwi': '/icons/kiwi-icon.svg',
  'fruit-plum-backend': '/icons/plum-icon.svg',
  'fruit-quince-server': '/icons/quince-icon.svg',
  'fruit-quince-mcp': '/icons/quince-icon.svg',
  'fruit-lemon': '/icons/lemon-icon.svg',
  'fruit-cherry': '/icons/cherry-icon.svg',
}

export const SERVICE_DEVICE_FALLBACK: Record<string, string> = {
  'llm-llama': 'gpu',
  'stt-qwen': 'cpu',
  'tts-pocket': 'cpu',
}

export function getServiceIcon(service: Pick<ServiceStatus, 'id' | 'icon' | 'fruit_id'>): string | null {
  return (
    service.icon ||
    SERVICE_ICON_MAP[service.id] ||
    (service.fruit_id ? `/icons/${service.fruit_id}-icon.svg` : null)
  )
}
