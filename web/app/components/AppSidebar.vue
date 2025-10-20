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

// Використовуйте ref для стану, як ви це робите, але переконайтеся,
// що він не змінюється асинхронно під час SSR.
const isChatsOpen = ref(false);
const isNotebooksOpen = ref(false);

// Класи для іконки, винесені в обчислюване властивість для чистоти
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
                <p class="w-full text-left">Chats1</p>
              </Button>
              <Button variant="ghost">
                <p class="w-full text-left">Chats1</p>
              </Button>
              <Button variant="ghost">
                <p class="w-full text-left">Chats1</p>
              </Button>
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
