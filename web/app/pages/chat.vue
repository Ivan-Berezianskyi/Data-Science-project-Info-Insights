<script setup lang="ts">
import { Textarea } from '~/components/ui/textarea';
import { Button } from '~/components/ui/button';
import { Input } from '~/components/ui/input';
import { SidebarInset } from '~/components/ui/sidebar';
import type { Message } from '~/types/api';
import { useMessages } from '~/composables/useMessages';
import { useChats } from '~/composables/useChats';

const route = useRoute();
const router = useRouter();
const { getMessagesByChat, createMessage } = useMessages();
const { getChat, createChat, updateChat } = useChats();

// Get chat_id from query parameter
const chatId = computed(() => {
  const id = route.query.chat_id;
  return id ? parseInt(id as string) : null;
});

// State
const messages = ref<Message[]>([]);
const currentChat = ref<any>(null);
const messageContent = ref('');
const isLoading = ref(false);
const isSending = ref(false);
const error = ref<string | null>(null);

// Chat name editing state
const isEditingName = ref(false);
const editedChatName = ref('');
const isUpdatingName = ref(false);

// Load chat and messages
const loadChat = async () => {
  if (!chatId.value) {
    // No chat_id means we're starting a new chat
    messages.value = [];
    currentChat.value = null;
    return;
  }

  isLoading.value = true;
  error.value = null;

  try {
    // Load chat details
    currentChat.value = await getChat(chatId.value);
    
    // Load messages
    const response = await getMessagesByChat(chatId.value);
    messages.value = response.items;
  } catch (err: any) {
    error.value = err.message || 'Failed to load chat';
    console.error('Error loading chat:', err);
  } finally {
    isLoading.value = false;
  }
};

// Send message
const sendMessage = async () => {
  if (!messageContent.value.trim() || isSending.value) {
    return;
  }

  isSending.value = true;
  const content = messageContent.value.trim();
  messageContent.value = '';

  try {
    let targetChatId = chatId.value;

    // If no chat exists, create one first
    if (!targetChatId) {
      const newChat = await createChat({
        name: `Chat ${new Date().toLocaleDateString()}`,
        notebooks: [],
      });
      targetChatId = newChat.id;
      
      // Update URL with new chat_id
      router.replace({ path: '/chat', query: { chat_id: targetChatId } });
      
      // Update local state
      currentChat.value = { ...newChat, messages_count: 0 };
    }

    // Create the message
    const newMessage = await createMessage({
      chat_id: targetChatId,
      role: 'user',
      content: content,
    });
    
    messages.value.push(newMessage);
    
    // Update message count
    if (currentChat.value) {
      currentChat.value.messages_count = messages.value.length;
    }
    
    // Scroll to bottom after sending
    await nextTick();
    scrollToBottom();
  } catch (err: any) {
    error.value = err.message || 'Failed to send message';
    console.error('Error sending message:', err);
    messageContent.value = content; // Restore message on error
  } finally {
    isSending.value = false;
  }
};

// Scroll to bottom of messages
const scrollToBottom = () => {
  const messagesContainer = document.getElementById('messages-container');
  if (messagesContainer) {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
};

// Watch for chat_id changes
watch(() => route.query.chat_id, () => {
  loadChat();
}, { immediate: true });

// Format date for display
const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleString('uk-UA', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// Handle Enter key (Shift+Enter for new line, Enter to send)
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
};

// Start editing chat name
const startEditingName = () => {
  if (!chatId.value) return;
  editedChatName.value = currentChat.value?.name || '';
  isEditingName.value = true;
  nextTick(() => {
    const input = document.getElementById('chat-name-input') as HTMLInputElement;
    if (input) {
      input.focus();
      input.select();
    }
  });
};

// Save chat name
const saveChatName = async () => {
  if (!chatId.value || !currentChat.value || isUpdatingName.value) return;

  const newName = editedChatName.value.trim();
  
  // If name is empty or unchanged, just cancel editing
  if (!newName || newName === currentChat.value.name) {
    isEditingName.value = false;
    return;
  }

  isUpdatingName.value = true;
  try {
    const updatedChat = await updateChat(chatId.value, { name: newName });
    currentChat.value.name = updatedChat.name;
    isEditingName.value = false;
  } catch (err: any) {
    error.value = err.message || 'Failed to update chat name';
    console.error('Error updating chat name:', err);
  } finally {
    isUpdatingName.value = false;
  }
};

// Cancel editing chat name
const cancelEditingName = () => {
  isEditingName.value = false;
  editedChatName.value = '';
};

// Handle Enter key in name input
const handleNameInputKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    saveChatName();
  } else if (e.key === 'Escape') {
    e.preventDefault();
    cancelEditingName();
  }
};
</script>

<template>
  <SidebarInset>
    <div class="w-full h-dvh flex flex-col">
      <!-- Chat Header -->
      <div class="border-b p-4 flex items-center justify-between pl-14">
        <div class="flex-1 flex items-center gap-2">
          <div v-if="!isEditingName" class="flex items-center gap-2">
            <h2 class="text-xl font-bold">
              {{ currentChat?.name || (chatId ? `Chat #${chatId}` : 'New Chat') }}
            </h2>
            <Button
              v-if="chatId"
              variant="ghost"
              size="sm"
              @click="startEditingName"
              class="h-6 w-6 p-0"
            >
              <Icon size="16px" name="material-symbols:edit-outline" />
            </Button>
          </div>
          <div v-else class="flex items-center gap-2 flex-1">
            <Input
              id="chat-name-input"
              v-model="editedChatName"
              @keydown="handleNameInputKeyDown"
              @blur="saveChatName"
              class="flex-1 max-w-md"
              :disabled="isUpdatingName"
            />
            <Button
              variant="ghost"
              size="sm"
              @click="saveChatName"
              :disabled="isUpdatingName"
              class="h-8"
            >
              <Icon size="16px" name="material-symbols:check" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              @click="cancelEditingName"
              :disabled="isUpdatingName"
              class="h-8"
            >
              <Icon size="16px" name="material-symbols:close" />
            </Button>
          </div>
          <p class="text-sm text-gray-500 ml-2" v-if="currentChat && !isEditingName">
            {{ currentChat.messages_count }} messages
          </p>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="p-4 bg-red-100 text-red-700 border-b">
        {{ error }}
      </div>

      <!-- Messages Container -->
      <div
        id="messages-container"
        class="flex-1 overflow-y-auto p-4 space-y-4"
      >
        <!-- Loading State -->
        <div v-if="isLoading" class="flex justify-center items-center h-full">
          <p class="text-gray-500">Loading messages...</p>
        </div>

        <!-- Messages List -->
        <div v-else-if="messages.length > 0" class="space-y-4">
          <div
            v-for="message in messages"
            :key="message.id"
            class="flex"
            :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
          >
            <div
              class="max-w-[70%] rounded-lg p-3"
              :class="
                message.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : message.role === 'ai'
                  ? 'bg-gray-200 text-gray-900'
                  : 'bg-yellow-100 text-yellow-900'
              "
            >
              <div class="whitespace-pre-wrap">{{ message.content }}</div>
              <div
                class="text-xs mt-1 opacity-70"
                :class="message.role === 'user' ? 'text-white' : 'text-gray-600'"
              >
                {{ formatDate(message.created_at) }}
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="flex justify-center items-center h-full">
          <div class="text-center">
            <p class="text-2xl font-bold mb-4">Дай Боже здоровʼя!</p>
            <p class="text-gray-500">Start the conversation by sending a message!</p>
          </div>
        </div>
      </div>

      <!-- Message Input -->
      <div class="border-t p-4">
        <div class="flex items-end gap-2 max-w-4xl mx-auto">
          <Textarea
            v-model="messageContent"
            @keydown="handleKeyDown"
            placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
            class="flex-1 resize-none min-h-[60px] max-h-[200px]"
            :disabled="isSending"
          />
          <Button
            @click="sendMessage"
            :disabled="!messageContent.trim() || isSending"
            class="h-[60px] px-6"
          >
            <Icon
              v-if="!isSending"
              size="24px"
              name="material-symbols:mode-comment-outline"
            />
            <span v-else>Sending...</span>
          </Button>
        </div>
      </div>
    </div>
  </SidebarInset>
</template>