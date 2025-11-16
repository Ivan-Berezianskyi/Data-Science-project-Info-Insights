import type {
  Chat,
  ChatCreate,
  ChatUpdate,
  ChatDetail,
  PaginatedChatResponse,
} from '~/types/api'

export const useChats = () => {
  const config = useRuntimeConfig()
  const API_BASE_URL = config.public.apiBaseUrl
  const getAllChats = async (page?: number, page_size?: number): Promise<PaginatedChatResponse> => {
    const params = new URLSearchParams()
    if (page) params.append('page', page.toString())
    if (page_size) params.append('page_size', page_size.toString())
    
    const query = params.toString() ? `?${params.toString()}` : ''
    const response = await $fetch<PaginatedChatResponse>(`${API_BASE_URL}/api/chats/${query}`)
    return response
  }

  const getChat = async (chatId: number): Promise<ChatDetail> => {
    const response = await $fetch<ChatDetail>(`${API_BASE_URL}/api/chats/${chatId}`)
    return response
  }

  const createChat = async (chatData: ChatCreate): Promise<Chat> => {
    const response = await $fetch<Chat>(`${API_BASE_URL}/api/chats/`, {
      method: 'POST',
      body: chatData,
    })
    return response
  }

  const updateChat = async (chatId: number, chatData: ChatUpdate): Promise<Chat> => {
    const response = await $fetch<Chat>(`${API_BASE_URL}/api/chats/${chatId}`, {
      method: 'PUT',
      body: chatData,
    })
    return response
  }

  const deleteChat = async (chatId: number): Promise<void> => {
    await $fetch(`${API_BASE_URL}/api/chats/${chatId}`, {
      method: 'DELETE',
    })
  }

  return {
    getAllChats,
    getChat,
    createChat,
    updateChat,
    deleteChat,
  }
}

