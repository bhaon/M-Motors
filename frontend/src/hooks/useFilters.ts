'use client'

import { useState, useMemo } from 'react'
import { VEHICLES } from '@/data/vehicles'
import { Filters, ContratType, Vehicle } from '@/types'

const DEFAULT_FILTERS: Filters = {
  marque: '',
  modele: '',
  moteur: '',
  kmMax: null,
  prixMax: null,
  type: 'all',
}

export function useFilters() {
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS)

  const marques = useMemo(
    () => [...new Set(VEHICLES.map(v => v.make))].sort((a, b) => a.localeCompare(b)),
    []
  )

  const modeles = useMemo(
    () =>
      [...new Set(
        VEHICLES.filter(v => !filters.marque || v.make === filters.marque).map(v => v.model)
      )].sort((a, b) => a.localeCompare(b)),
 
    [filters.marque]
  )

  const filtered = useMemo(() => {
    return VEHICLES.filter(v => {
      if (filters.marque && v.make !== filters.marque) return false
      if (filters.modele && v.model !== filters.modele) return false
      if (filters.moteur && v.moteur !== filters.moteur) return false
      if (filters.kmMax !== null && v.km > filters.kmMax) return false
      if (filters.prixMax !== null && v.prix > filters.prixMax) return false
      if (filters.type === 'achat' && v.lld) return false
      if (filters.type === 'lld' && !v.lld) return false
      return true
    })
  }, [filters])

  const setType = (type: ContratType) =>
    setFilters(f => ({ ...f, type }))

  const setField = (field: keyof Filters, value: string | number | null) =>
    setFilters(f => ({
      ...f,
      [field]: value,
      ...(field === 'marque' ? { modele: '' } : {}),
    }))

  const reset = () => setFilters(DEFAULT_FILTERS)

  return { filters, filtered, marques, modeles, setType, setField, reset }
}
