<script setup lang="ts">
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import type { Chat } from "~/types/api";
import { useChats } from "~/composables/useChats";

const { getAllChats, createChat } = useChats();

const isChatsOpen = ref(false);
const isNotebooksOpen = ref(false);

const route = useRoute();
const router = useRouter();

const isChatDisabled = computed(() => route.fullPath == "/chat");
const isNotebookDisabled = computed(() => route.fullPath == "/notebooks");

// Chats state
const chats = ref<Chat[]>([]);
const isLoadingChats = ref(false);
const isCreatingChat = ref(false);
const chatsError = ref<string | null>(null);

// Load chats
const loadChats = async () => {
  isLoadingChats.value = true;
  chatsError.value = null;

  try {
    const response = await getAllChats();
    chats.value = response.items;
  } catch (err: any) {
    chatsError.value = err.message || "Failed to load chats";
    console.error("Error loading chats:", err);
  } finally {
    isLoadingChats.value = false;
  }
};

// Create new chat
const handleCreateChat = async () => {
  if (isCreatingChat.value) return;

  isCreatingChat.value = true;
  try {
    const newChat = await createChat({
      name: `Chat ${new Date().toLocaleDateString()}`,
      notebooks: [],
    });
    
    // Add to list and navigate to it
    chats.value.unshift(newChat);
    router.push({ path: "/chat", query: { chat_id: newChat.id } });
  } catch (err: any) {
    chatsError.value = err.message || "Failed to create chat";
    console.error("Error creating chat:", err);
  } finally {
    isCreatingChat.value = false;
  }
};

// Navigate to chat
const navigateToChat = (chatId: number) => {
  router.push({ path: "/chat", query: { chat_id: chatId } });
};

// Check if chat is active
const isChatActive = (chatId: number) => {
  return route.query.chat_id === chatId.toString();
};

// Format chat name for display
const getChatDisplayName = (chat: Chat) => {
  return chat.name || `Chat #${chat.id}`;
};

// Load chats on mount
onMounted(() => {
  loadChats();
});

// Refresh chats when route changes (in case a chat was created elsewhere)
watch(() => route.query.chat_id, (newChatId) => {
  if (route.path === "/chat") {
    loadChats();
    // Expand chats section when a chat is selected
    if (newChatId) {
      isChatsOpen.value = true;
    }
  }
});

const chatsIconClasses = computed(() => [
  "transition-transform",
  "duration-300",
  "ease-in-out",
  { "rotate-180": isChatsOpen.value },
]);

const notebooksIconClasses = computed(() => [
  "transition-transform",
  "duration-300",
  "ease-in-out",
  { "rotate-180": isNotebooksOpen.value },
]);
</script>

<template>
  <Sidebar>
    <SidebarHeader>
      <h1 class="w-full text-center text-2xl font-bold">Info Insights</h1>
    </SidebarHeader>
    <SidebarContent>
      <SidebarGroup class="gap-2">
        <Collapsible v-model:open="isChatsOpen">
          <div class="flex items-center gap-x-1">
            <CollapsibleTrigger as-child class="grow my-2">
              <Button variant="outline" class="grow flex justify-between">
                <p class="text-left">Chats</p>
                <Icon
                  size="40px"
                  name="material-symbols:arrow-drop-down-rounded"
                  :class="chatsIconClasses"
                />
              </Button> </CollapsibleTrigger
            ><Button
              variant="default"
              :disabled="isCreatingChat"
              @click="handleCreateChat"
              class="text-white w-[40px] text-xl text-center flex items-center justify-center"
            >
              <Icon
                v-if="!isCreatingChat"
                size="20px"
                name="material-symbols:add"
              />
              <span v-else class="text-sm">...</span>
            </Button>
          </div>

          <CollapsibleContent class="pl-4 py-1">
            <div
              class="flex flex-col w-full gap-2 border-l-2 border-l-gray-200 pl-2 border-dashed"
            >
              <!-- Error Message -->
              <div v-if="chatsError" class="text-xs text-red-600 p-2">
                {{ chatsError }}
              </div>

              <!-- Loading State -->
              <div v-if="isLoadingChats" class="text-xs text-gray-500 p-2">
                Loading chats...
              </div>

              <!-- Chats List -->
              <template v-else-if="chats.length > 0">
                <Button
                  v-for="chat in chats"
                  :key="chat.id"
                  variant="ghost"
                  @click="navigateToChat(chat.id)"
                  :class="[
                    'w-full text-left justify-start',
                    isChatActive(chat.id) && 'bg-gray-100 font-semibold'
                  ]"
                >
                  <p class="w-full text-left truncate">
                    {{ getChatDisplayName(chat) }}
                  </p>
                </Button>
              </template>

              <!-- Empty State -->
              <div v-else class="text-xs text-gray-500 p-2">
                No chats yet. Create one!
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>

        <Collapsible v-model:open="isNotebooksOpen">
          <div class="flex items-center gap-x-1">
            <CollapsibleTrigger as-child class="grow my-2">
              <Button variant="outline" class="grow flex justify-between">
                <p class="text-left">Notebooks</p>
                <Icon
                  size="40px"
                  name="material-symbols:arrow-drop-down-rounded"
                  :class="notebooksIconClasses"
                />
              </Button> </CollapsibleTrigger
            ><Button
              variant="default"
              :disabled="isNotebookDisabled"
              @click="() => router.push({ path : '/notebooks'})"
              class="text-white w-[40px] text-xl text-center flex items-center justify-center"
            >
              <p>+</p>
            </Button>
          </div>
          <CollapsibleContent class="pl-4 py-1">
            <div
              class="flex flex-col w-full gap-2 border-l-2 border-l-gray-200 pl-2 border-dashed"
            >
              <Button variant="ghost">
                <p class="w-full text-left">Notebook1</p>
              </Button>
              <Button variant="ghost">
                <p class="w-full text-left">Notebook1</p>
              </Button>
              <Button variant="ghost">
                <p class="w-full text-left">Notebook1</p>
              </Button>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </SidebarGroup>
      <SidebarGroup />
    </SidebarContent>
    <SidebarFooter>
      <div class="flex gap-x-1">
        <Button variant="outline" class="flex-1 flex justify-between"
          ><Icon size="30px" name="material-symbols:account-circle"></Icon>
          <p>User</p></Button
        >
        <Button
          ><Icon
            size="30px"
            name="material-symbols:display-settings-outline"
          ></Icon
        ></Button>
      </div>
    </SidebarFooter>
  </Sidebar>
</template>
