// API Types matching backend schemas

export type MessageRole = 'user' | 'ai' | 'system'

export interface Chat {
  id: number
  name?: string | null
  notebooks: string[]
  created_at: string
  updated_at: string
}

export interface ChatCreate {
  name?: string | null
  notebooks?: string[]
}

export interface ChatUpdate {
  name?: string | null
  notebooks?: string[] | null
}

export interface ChatDetail extends Chat {
  messages_count: number
}

export interface Message {
  id: number
  chat_id: number
  role: MessageRole
  content: string
  created_at: string
  updated_at: string
}

export interface MessageCreate {
  chat_id: number
  role: MessageRole
  content: string
}

export interface MessageUpdate {
  content?: string
  role?: MessageRole
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface PaginatedChatResponse extends PaginatedResponse<Chat> {}
export interface PaginatedMessageResponse extends PaginatedResponse<Message> {}

