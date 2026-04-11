<template>
  <div class="px-3 pt-4 pb-1">
    <p class="text-[10px] font-semibold text-claude-dust uppercase tracking-[0.12em]">{{ label }}</p>
  </div>
</template>

<script setup>
defineProps({ label: String })
</script>
