import { useState } from 'react'
import { toast } from 'sonner'
import { Plus, Pencil, Trash2, FolderOpen } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  useServices,
  useCreateService,
  useUpdateService,
  useDeleteService,
  useCategories,
  useCreateCategory,
  useUpdateCategory,
  useDeleteCategory,
} from '@/hooks/useServices'
import type { Service, ServiceCategory } from '@/types'

// --- Форма для услуги ---

interface ServiceFormData {
  name: string
  description: string
  price: string
  duration_minutes: string
  category_id: string
  sort_order: string
}

const emptyServiceForm: ServiceFormData = {
  name: '',
  description: '',
  price: '',
  duration_minutes: '60',
  category_id: '',
  sort_order: '0',
}

// --- Форма для категории ---

interface CategoryFormData {
  name: string
  sort_order: string
}

const emptyCategoryForm: CategoryFormData = {
  name: '',
  sort_order: '0',
}

/**
 * Страница управления услугами — весь CRUD для услуг и категорий
 * Таблица с фильтрацией, диалоги создания/редактирования, удаление с подтверждением
 */
export default function ServicesPage() {
  // хуки для данных
  const { data: services, isLoading: servicesLoading } = useServices()
  const { data: categories, isLoading: categoriesLoading } = useCategories()
  const createService = useCreateService()
  const updateService = useUpdateService()
  const deleteService = useDeleteService()
  const createCategory = useCreateCategory()
  const updateCategory = useUpdateCategory()
  const deleteCategory = useDeleteCategory()

  // состояние диалогов для услуг
  const [serviceDialogOpen, setServiceDialogOpen] = useState(false)
  const [editingService, setEditingService] = useState<Service | null>(null)
  const [serviceForm, setServiceForm] = useState<ServiceFormData>(emptyServiceForm)
  const [deleteServiceId, setDeleteServiceId] = useState<string | null>(null)

  // состояние диалогов для категорий
  const [categoryDialogOpen, setCategoryDialogOpen] = useState(false)
  const [editingCategory, setEditingCategory] = useState<ServiceCategory | null>(null)
  const [categoryForm, setCategoryForm] = useState<CategoryFormData>(emptyCategoryForm)
  const [deleteCategoryId, setDeleteCategoryId] = useState<string | null>(null)
  const [showCategories, setShowCategories] = useState(false)

  // --- обработчики для услуг ---

  /** Открыть диалог на добавление новой услуги */
  const handleAddService = () => {
    setEditingService(null)
    setServiceForm(emptyServiceForm)
    setServiceDialogOpen(true)
  }

  /** Открыть диалог на редактирование существующей услуги */
  const handleEditService = (service: Service) => {
    setEditingService(service)
    setServiceForm({
      name: service.name,
      description: service.description ?? '',
      price: String(service.price),
      duration_minutes: String(service.duration_minutes),
      category_id: service.category_id ?? '',
      sort_order: String(service.sort_order),
    })
    setServiceDialogOpen(true)
  }

  /** Сохранить услугу — создание или обновление */
  const handleSaveService = () => {
    const data = {
      name: serviceForm.name,
      description: serviceForm.description || null,
      price: parseFloat(serviceForm.price),
      duration_minutes: parseInt(serviceForm.duration_minutes),
      category_id: serviceForm.category_id || null,
      sort_order: parseInt(serviceForm.sort_order) || 0,
    }

    if (editingService) {
      updateService.mutate(
        { id: editingService.id, data },
        {
          onSuccess: () => {
            toast.success('Услуга обновлена')
            setServiceDialogOpen(false)
          },
          onError: () => toast.error('Не удалось обновить услугу'),
        },
      )
    } else {
      createService.mutate(data, {
        onSuccess: () => {
          toast.success('Услуга создана')
          setServiceDialogOpen(false)
        },
        onError: () => toast.error('Не удалось создать услугу'),
      })
    }
  }

  /** Удалить услугу — после подтверждения */
  const handleConfirmDeleteService = () => {
    if (!deleteServiceId) return
    deleteService.mutate(deleteServiceId, {
      onSuccess: () => {
        toast.success('Услуга удалена')
        setDeleteServiceId(null)
      },
      onError: () => toast.error('Не удалось удалить услугу'),
    })
  }

  /** Переключить активность услуги — вкл/выкл */
  const handleToggleActive = (service: Service) => {
    updateService.mutate(
      { id: service.id, data: { is_active: !service.is_active } },
      {
        onSuccess: () =>
          toast.success(service.is_active ? 'Услуга деактивирована' : 'Услуга активирована'),
        onError: () => toast.error('Не удалось изменить статус'),
      },
    )
  }

  // --- обработчики для категорий ---

  /** Открыть диалог создания категории */
  const handleAddCategory = () => {
    setEditingCategory(null)
    setCategoryForm(emptyCategoryForm)
    setCategoryDialogOpen(true)
  }

  /** Открыть диалог редактирования категории */
  const handleEditCategory = (category: ServiceCategory) => {
    setEditingCategory(category)
    setCategoryForm({
      name: category.name,
      sort_order: String(category.sort_order),
    })
    setCategoryDialogOpen(true)
  }

  /** Сохранить категорию */
  const handleSaveCategory = () => {
    const data = {
      name: categoryForm.name,
      sort_order: parseInt(categoryForm.sort_order) || 0,
    }

    if (editingCategory) {
      updateCategory.mutate(
        { id: editingCategory.id, data },
        {
          onSuccess: () => {
            toast.success('Категория обновлена')
            setCategoryDialogOpen(false)
          },
          onError: () => toast.error('Не удалось обновить категорию'),
        },
      )
    } else {
      createCategory.mutate(data, {
        onSuccess: () => {
          toast.success('Категория создана')
          setCategoryDialogOpen(false)
        },
        onError: () => toast.error('Не удалось создать категорию'),
      })
    }
  }

  /** Удалить категорию */
  const handleConfirmDeleteCategory = () => {
    if (!deleteCategoryId) return
    deleteCategory.mutate(deleteCategoryId, {
      onSuccess: () => {
        toast.success('Категория удалена')
        setDeleteCategoryId(null)
      },
      onError: () => toast.error('Не удалось удалить категорию'),
    })
  }

  const isLoading = servicesLoading || categoriesLoading

  return (
    <div className="space-y-6">
      {/* Заголовок и кнопки */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Услуги</h1>
          <p className="text-muted-foreground">Управление услугами и категориями</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowCategories(!showCategories)}>
            <FolderOpen className="mr-1.5 h-4 w-4" />
            Категории
          </Button>
          <Button onClick={handleAddService}>
            <Plus className="mr-1.5 h-4 w-4" />
            Добавить услугу
          </Button>
        </div>
      </div>

      {/* Блок категорий — схлопываемый */}
      {showCategories && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Категории</CardTitle>
            <Button size="sm" onClick={handleAddCategory}>
              <Plus className="mr-1 h-3.5 w-3.5" />
              Добавить
            </Button>
          </CardHeader>
          <CardContent>
            {categoriesLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-10 w-full" />
                ))}
              </div>
            ) : !categories?.length ? (
              <p className="text-sm text-muted-foreground py-4">Категорий пока нет</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Название</TableHead>
                    <TableHead className="w-24">Порядок</TableHead>
                    <TableHead className="w-24 text-right">Действия</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {categories.map((cat) => (
                    <TableRow key={cat.id}>
                      <TableCell className="font-medium">{cat.name}</TableCell>
                      <TableCell>{cat.sort_order}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => handleEditCategory(cat)}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => setDeleteCategoryId(cat.id)}
                          >
                            <Trash2 className="h-3.5 w-3.5 text-destructive" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}

      {/* Таблица услуг */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !services?.length ? (
            <div className="flex flex-col items-center justify-center py-12">
              <p className="text-muted-foreground mb-4">Услуг пока нет</p>
              <Button onClick={handleAddService}>
                <Plus className="mr-1.5 h-4 w-4" />
                Добавить первую услугу
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Название</TableHead>
                  <TableHead className="hidden sm:table-cell">Категория</TableHead>
                  <TableHead>Цена</TableHead>
                  <TableHead className="hidden md:table-cell">Длительность</TableHead>
                  <TableHead>Статус</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {services.map((service) => (
                  <TableRow key={service.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{service.name}</p>
                        {service.description && (
                          <p className="text-xs text-muted-foreground truncate max-w-[200px]">
                            {service.description}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="hidden sm:table-cell">
                      {service.category_name ? (
                        <Badge variant="secondary">{service.category_name}</Badge>
                      ) : (
                        <span className="text-muted-foreground text-xs">—</span>
                      )}
                    </TableCell>
                    <TableCell>{service.price.toLocaleString('ru-RU')} ₽</TableCell>
                    <TableCell className="hidden md:table-cell">
                      {service.duration_minutes} мин
                    </TableCell>
                    <TableCell>
                      <Switch
                        checked={service.is_active}
                        onCheckedChange={() => handleToggleActive(service)}
                        size="sm"
                      />
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => handleEditService(service)}
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => setDeleteServiceId(service.id)}
                        >
                          <Trash2 className="h-3.5 w-3.5 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Диалог создания/редактирования услуги */}
      <Dialog open={serviceDialogOpen} onOpenChange={setServiceDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{editingService ? 'Редактировать услугу' : 'Новая услуга'}</DialogTitle>
            <DialogDescription>
              {editingService
                ? 'Измените параметры услуги'
                : 'Заполните данные для создания новой услуги'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="svc-name">Название</Label>
              <Input
                id="svc-name"
                value={serviceForm.name}
                onChange={(e) => setServiceForm({ ...serviceForm, name: e.target.value })}
                placeholder="Например: Стрижка мужская"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="svc-desc">Описание</Label>
              <Textarea
                id="svc-desc"
                value={serviceForm.description}
                onChange={(e) => setServiceForm({ ...serviceForm, description: e.target.value })}
                placeholder="Краткое описание услуги"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="svc-price">Цена (₽)</Label>
                <Input
                  id="svc-price"
                  type="number"
                  min="0"
                  step="100"
                  value={serviceForm.price}
                  onChange={(e) => setServiceForm({ ...serviceForm, price: e.target.value })}
                  placeholder="1000"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="svc-duration">Длительность (мин)</Label>
                <Input
                  id="svc-duration"
                  type="number"
                  min="5"
                  step="5"
                  value={serviceForm.duration_minutes}
                  onChange={(e) =>
                    setServiceForm({ ...serviceForm, duration_minutes: e.target.value })
                  }
                  placeholder="60"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Категория</Label>
              <Select
                value={serviceForm.category_id}
                onValueChange={(val) => setServiceForm({ ...serviceForm, category_id: val as string })}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Без категории" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Без категории</SelectItem>
                  {(categories ?? []).map((cat) => (
                    <SelectItem key={cat.id} value={cat.id}>
                      {cat.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="svc-order">Порядок сортировки</Label>
              <Input
                id="svc-order"
                type="number"
                value={serviceForm.sort_order}
                onChange={(e) => setServiceForm({ ...serviceForm, sort_order: e.target.value })}
                placeholder="0"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setServiceDialogOpen(false)}
            >
              Отмена
            </Button>
            <Button
              onClick={handleSaveService}
              disabled={
                !serviceForm.name || !serviceForm.price || createService.isPending || updateService.isPending
              }
            >
              {createService.isPending || updateService.isPending ? 'Сохраняем...' : 'Сохранить'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Подтверждение удаления услуги */}
      <AlertDialog
        open={!!deleteServiceId}
        onOpenChange={(open) => !open && setDeleteServiceId(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить услугу?</AlertDialogTitle>
            <AlertDialogDescription>
              Услуга будет удалена безвозвратно. Существующие записи на нее сохранятся.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDeleteService}
              className="bg-destructive/10 text-destructive hover:bg-destructive/20"
            >
              {deleteService.isPending ? 'Удаляем...' : 'Удалить'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Диалог создания/редактирования категории */}
      <Dialog open={categoryDialogOpen} onOpenChange={setCategoryDialogOpen}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>
              {editingCategory ? 'Редактировать категорию' : 'Новая категория'}
            </DialogTitle>
            <DialogDescription>
              Категории помогают группировать услуги
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="cat-name">Название</Label>
              <Input
                id="cat-name"
                value={categoryForm.name}
                onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
                placeholder="Например: Стрижки"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="cat-order">Порядок сортировки</Label>
              <Input
                id="cat-order"
                type="number"
                value={categoryForm.sort_order}
                onChange={(e) => setCategoryForm({ ...categoryForm, sort_order: e.target.value })}
                placeholder="0"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCategoryDialogOpen(false)}>
              Отмена
            </Button>
            <Button
              onClick={handleSaveCategory}
              disabled={
                !categoryForm.name || createCategory.isPending || updateCategory.isPending
              }
            >
              {createCategory.isPending || updateCategory.isPending ? 'Сохраняем...' : 'Сохранить'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Подтверждение удаления категории */}
      <AlertDialog
        open={!!deleteCategoryId}
        onOpenChange={(open) => !open && setDeleteCategoryId(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить категорию?</AlertDialogTitle>
            <AlertDialogDescription>
              Услуги в этой категории останутся, но будут без категории.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDeleteCategory}
              className="bg-destructive/10 text-destructive hover:bg-destructive/20"
            >
              {deleteCategory.isPending ? 'Удаляем...' : 'Удалить'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
