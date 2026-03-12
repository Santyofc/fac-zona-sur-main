<template>
  <NuxtLayout>
    <h1 class="fcr-page-title">Nueva Factura Electrónica</h1>
    <p class="fcr-page-subtitle">Crea un comprobante electrónico compatible con Hacienda v4.4</p>

    <InvoiceForm @created="onCreated" @cancel="() => $router.push('/invoices')" />
  </NuxtLayout>
</template>

<script setup lang="ts">
const router = useRouter()

async function onCreated(id: string) {
  await router.push(`/invoices/${id}`)
}

useHead({ title: 'Nueva Factura — Factura CR' })
</script>
