import type {
  Message,
  MessageCreate,
  MessageUpdate,
  PaginatedMessageResponse,
} from '~/types/api'

export const useMessages = () => {
  const config = useRuntimeConfig()
  const API_BASE_URL = config.public.apiBaseUrl
  const getMessagesByChat = async (
    chatId: number,
    page?: number,
    page_size?: number
  ): Promise<PaginatedMessageResponse> => {
    const params = new URLSearchParams()
    if (page) params.append('page', page.toString())
    if (page_size) params.append('page_size', page_size.toString())
    
    const query = params.toString() ? `?${params.toString()}` : ''
    const response = await $fetch<PaginatedMessageResponse>(
      `${API_BASE_URL}/api/messages/chat/${chatId}${query}`
    )
    return response
  }

  const getMessage = async (messageId: number): Promise<Message> => {
    const response = await $fetch<Message>(`${API_BASE_URL}/api/messages/${messageId}`)
    return response
  }

  const createMessage = async (messageData: MessageCreate): Promise<Message> => {
    const response = await $fetch<Message>(`${API_BASE_URL}/api/messages/`, {
      method: 'POST',
      body: messageData,
    })
    return response
  }

  const updateMessage = async (messageId: number, messageData: MessageUpdate): Promise<Message> => {
    const response = await $fetch<Message>(`${API_BASE_URL}/api/messages/${messageId}`, {
      method: 'PUT',
      body: messageData,
    })
    return response
  }

  const deleteMessage = async (messageId: number): Promise<void> => {
    await $fetch(`${API_BASE_URL}/api/messages/${messageId}`, {
      method: 'DELETE',
    })
  }

  return {
    getMessagesByChat,
    getMessage,
    createMessage,
    updateMessage,
    deleteMessage,
  }
}

