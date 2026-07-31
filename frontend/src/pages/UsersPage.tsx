import { useState } from 'react'
import { toast } from 'sonner'
import { Plus, Pencil, Trash2, Copy, Shield, ShieldCheck } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
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
import { useAuth } from '@/contexts/AuthContext'
import { useUsers, useCreateUser, useUpdateUser, useDeleteUser } from '@/hooks/useUsers'
import type { User, UserRole } from '@/types'

// --- форма создания ---

interface CreateFormData {
  email: string
  name: string
  role: UserRole
}

const emptyCreateForm: CreateFormData = {
  email: '',
  name: '',
  role: 'operator',
}

// --- форма редактирования ---

interface EditFormData {
  name: string
  role: UserRole
  is_active: boolean
}

/**
 * Страница управления пользователями (операторами)
 * CRUD для юзеров, показ временного пароля после создания
 */
export default function UsersPage() {
  const { user: currentUser } = useAuth()
  const { data: users, isLoading } = useUsers()
  const createUser = useCreateUser()
  const updateUser = useUpdateUser()
  const deleteUser = useDeleteUser()

  // диалог создания
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [createForm, setCreateForm] = useState<CreateFormData>(emptyCreateForm)

  // диалог с временным паролем
  const [tempPassword, setTempPassword] = useState<string | null>(null)
  const [createdUserName, setCreatedUserName] = useState('')

  // диалог редактирования
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [editForm, setEditForm] = useState<EditFormData>({
    name: '',
    role: 'operator',
    is_active: true,
  })

  // удаление
  const [deleteId, setDeleteId] = useState<string | null>(null)

  /** Открыть создание */
  const handleOpenCreate = () => {
    setCreateForm(emptyCreateForm)
    setCreateDialogOpen(true)
  }

  /** Создать пользователя */
  const handleCreate = () => {
    createUser.mutate(createForm, {
      onSuccess: (result) => {
        setCreateDialogOpen(false)
        setCreatedUserName(createForm.name)
        setTempPassword(result.temp_password)
        toast.success('Пользователь создан')
      },
      onError: () => toast.error('Не удалось создать пользователя'),
    })
  }

  /** Открыть редактирование */
  const handleOpenEdit = (user: User) => {
    setEditingUser(user)
    setEditForm({
      name: user.name,
      role: user.role,
      is_active: user.is_active,
    })
    setEditDialogOpen(true)
  }

  /** Сохранить редактирование */
  const handleSaveEdit = () => {
    if (!editingUser) return
    updateUser.mutate(
      { id: editingUser.id, data: editForm },
      {
        onSuccess: () => {
          toast.success('Пользователь обновлен')
          setEditDialogOpen(false)
        },
        onError: () => toast.error('Не удалось обновить пользователя'),
      },
    )
  }

  /** Удалить пользователя */
  const handleConfirmDelete = () => {
    if (!deleteId) return
    deleteUser.mutate(deleteId, {
      onSuccess: () => {
        toast.success('Пользователь удален')
        setDeleteId(null)
      },
      onError: () => toast.error('Не удалось удалить пользователя'),
    })
  }

  /** Скопировать пароль в буфер */
  const handleCopyPassword = () => {
    if (tempPassword) {
      navigator.clipboard.writeText(tempPassword).then(() => {
        toast.success('Пароль скопирован')
      })
    }
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Пользователи</h1>
          <p className="text-muted-foreground">Управление операторами системы</p>
        </div>
        <Button onClick={handleOpenCreate}>
          <Plus className="mr-1.5 h-4 w-4" />
          Добавить пользователя
        </Button>
      </div>

      {/* Таблица пользователей */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !users?.length ? (
            <div className="py-12 text-center text-muted-foreground">
              Пользователей не найдено
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Имя</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead className="hidden sm:table-cell">Роль</TableHead>
                  <TableHead>Статус</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user) => {
                  const isSelf = user.id === currentUser?.id
                  return (
                    <TableRow key={user.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{user.name}</span>
                          {isSelf && (
                            <Badge variant="outline" className="text-xs">
                              Вы
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-muted-foreground">{user.email}</TableCell>
                      <TableCell className="hidden sm:table-cell">
                        <div className="flex items-center gap-1.5">
                          {user.role === 'owner' ? (
                            <>
                              <ShieldCheck className="h-3.5 w-3.5 text-primary" />
                              <span className="text-sm">Владелец</span>
                            </>
                          ) : (
                            <>
                              <Shield className="h-3.5 w-3.5 text-muted-foreground" />
                              <span className="text-sm">Оператор</span>
                            </>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        {user.is_active ? (
                          <Badge variant="secondary">Активен</Badge>
                        ) : (
                          <Badge variant="destructive">Отключен</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => handleOpenEdit(user)}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                          {!isSelf && (
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              onClick={() => setDeleteId(user.id)}
                            >
                              <Trash2 className="h-3.5 w-3.5 text-destructive" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Диалог создания пользователя */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Новый пользователь</DialogTitle>
            <DialogDescription>
              Пользователь получит временный пароль для входа
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="usr-email">Email</Label>
              <Input
                id="usr-email"
                type="email"
                value={createForm.email}
                onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                placeholder="operator@example.com"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="usr-name">Имя</Label>
              <Input
                id="usr-name"
                value={createForm.name}
                onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                placeholder="Иван Иванов"
              />
            </div>
            <div className="space-y-2">
              <Label>Роль</Label>
              <Select
                value={createForm.role}
                onValueChange={(val) => setCreateForm({ ...createForm, role: val as UserRole })}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="operator">Оператор</SelectItem>
                  <SelectItem value="owner">Владелец</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              Отмена
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!createForm.email || !createForm.name || createUser.isPending}
            >
              {createUser.isPending ? 'Создаем...' : 'Создать'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Диалог с временным паролем */}
      <Dialog open={!!tempPassword} onOpenChange={(open) => !open && setTempPassword(null)}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Пользователь создан</DialogTitle>
            <DialogDescription>
              Передайте этот временный пароль пользователю {createdUserName}. При первом входе
              система попросит сменить пароль.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="flex items-center gap-2 rounded-lg bg-muted p-3">
              <code className="flex-1 text-sm font-mono select-all">{tempPassword}</code>
              <Button variant="outline" size="icon-sm" onClick={handleCopyPassword}>
                <Copy className="h-3.5 w-3.5" />
              </Button>
            </div>
            <p className="text-xs text-destructive">
              Этот пароль показывается только один раз. Скопируйте его сейчас.
            </p>
          </div>
          <DialogFooter>
            <Button onClick={() => setTempPassword(null)}>Понятно</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Диалог редактирования */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Редактировать пользователя</DialogTitle>
            <DialogDescription>
              Изменение данных пользователя {editingUser?.email}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">Имя</Label>
              <Input
                id="edit-name"
                value={editForm.name}
                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Роль</Label>
              <Select
                value={editForm.role}
                onValueChange={(val) => setEditForm({ ...editForm, role: val as UserRole })}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="operator">Оператор</SelectItem>
                  <SelectItem value="owner">Владелец</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Статус</Label>
              <Select
                value={editForm.is_active ? 'active' : 'inactive'}
                onValueChange={(val) =>
                  setEditForm({ ...editForm, is_active: val === 'active' })
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Активен</SelectItem>
                  <SelectItem value="inactive">Отключен</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              Отмена
            </Button>
            <Button
              onClick={handleSaveEdit}
              disabled={!editForm.name || updateUser.isPending}
            >
              {updateUser.isPending ? 'Сохраняем...' : 'Сохранить'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Подтверждение удаления */}
      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить пользователя?</AlertDialogTitle>
            <AlertDialogDescription>
              Пользователь потеряет доступ к системе. Это действие нельзя отменить.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              className="bg-destructive/10 text-destructive hover:bg-destructive/20"
            >
              {deleteUser.isPending ? 'Удаляем...' : 'Удалить'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
