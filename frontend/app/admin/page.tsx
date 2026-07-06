"use client";

import { KeyRound, Plus, RefreshCw, Save, ShieldCheck, Trash2, UserPlus, Users } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

import {
  createAdminMembership,
  createAdminRole,
  createAdminUser,
  deleteAdminMembership,
  getAdminMemberships,
  getAdminRoles,
  getAdminUsers,
  getMatters,
  rotateAdminUserKey,
  updateAdminMembership,
  updateAdminUser,
  type AdminMembership,
  type AdminRole,
  type AdminUser,
  type Matter,
} from "../../lib/api";

export default function AdminPage() {
  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [matters, setMatters] = useState<Matter[]>([]);
  const [memberships, setMemberships] = useState<AdminMembership[]>([]);
  const [roleName, setRoleName] = useState("");
  const [roleDescription, setRoleDescription] = useState("");
  const [roleIsAdmin, setRoleIsAdmin] = useState(false);
  const [userEmail, setUserEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [organization, setOrganization] = useState("");
  const [tenantId, setTenantId] = useState("");
  const [newUserRoleId, setNewUserRoleId] = useState<number | undefined>();
  const [membershipUserId, setMembershipUserId] = useState<number | undefined>();
  const [membershipMatterId, setMembershipMatterId] = useState<number | undefined>();
  const [membershipRole, setMembershipRole] = useState("reviewer");
  const [visibleApiKey, setVisibleApiKey] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);

  const activeUsers = useMemo(() => users.filter((user) => user.is_active).length, [users]);
  const adminUsers = useMemo(() => users.filter((user) => user.role_name === "admin").length, [users]);

  async function refresh() {
    setError(null);
    const [roleRows, userRows, matterRows, membershipRows] = await Promise.all([
      getAdminRoles(),
      getAdminUsers(),
      getMatters(),
      getAdminMemberships(),
    ]);
    setRoles(roleRows);
    setUsers(userRows);
    setMatters(matterRows);
    setMemberships(membershipRows);
    if (!newUserRoleId && roleRows[0]) {
      setNewUserRoleId(roleRows[0].id);
    }
    if (!membershipUserId && userRows[0]) {
      setMembershipUserId(userRows[0].id);
    }
    if (!membershipMatterId && matterRows[0]) {
      setMembershipMatterId(matterRows[0].id);
    }
  }

  useEffect(() => {
    void refresh().catch(() => setError("Unable to load admin data"));
  }, []);

  async function runAction(action: () => Promise<string | void>) {
    setIsBusy(true);
    setError(null);
    setStatus(null);
    try {
      const message = await action();
      if (message) {
        setStatus(message);
      }
    } catch {
      setError("Admin action failed");
    } finally {
      setIsBusy(false);
    }
  }

  async function submitRole() {
    const trimmed = roleName.trim();
    if (!trimmed) {
      setError("Role name is required");
      return;
    }
    await runAction(async () => {
      await createAdminRole({
        name: trimmed,
        description: roleDescription.trim() || undefined,
        is_admin: roleIsAdmin,
      });
      setRoleName("");
      setRoleDescription("");
      setRoleIsAdmin(false);
      await refresh();
      return `Created role ${trimmed}`;
    });
  }

  async function submitUser() {
    const email = userEmail.trim();
    const name = displayName.trim();
    if (!email || !name) {
      setError("Email and display name are required");
      return;
    }
    await runAction(async () => {
      const response = await createAdminUser({
        email,
        display_name: name,
        role_id: newUserRoleId,
        organization: organization.trim() || undefined,
        tenant_id: tenantId.trim() || undefined,
        is_active: true,
      });
      setVisibleApiKey(response.api_key);
      setUserEmail("");
      setDisplayName("");
      setOrganization("");
      setTenantId("");
      await refresh();
      return `Created user ${response.user.email}`;
    });
  }

  async function saveUser(user: AdminUser) {
    await runAction(async () => {
      await updateAdminUser(user.id, {
        display_name: user.display_name,
        role_id: user.role_id,
        organization: user.organization,
        tenant_id: user.tenant_id,
        is_active: user.is_active,
      });
      await refresh();
      return `Updated ${user.email}`;
    });
  }

  async function rotateKey(user: AdminUser) {
    await runAction(async () => {
      const response = await rotateAdminUserKey(user.id);
      setVisibleApiKey(response.api_key);
      await refresh();
      return `Rotated key for ${user.email}`;
    });
  }

  async function submitMembership() {
    if (!membershipUserId || !membershipMatterId || !membershipRole.trim()) {
      setError("User, matter, and assignment role are required");
      return;
    }
    await runAction(async () => {
      await createAdminMembership({
        user_id: membershipUserId,
        matter_id: membershipMatterId,
        role: membershipRole.trim(),
      });
      await refresh();
      return "Created matter assignment";
    });
  }

  async function saveMembership(membership: AdminMembership) {
    await runAction(async () => {
      await updateAdminMembership(membership.id, membership.role);
      await refresh();
      return "Updated matter assignment";
    });
  }

  async function removeMembership(membership: AdminMembership) {
    await runAction(async () => {
      await deleteAdminMembership(membership.id);
      await refresh();
      return "Deleted matter assignment";
    });
  }

  function updateUserRow(userId: number, patch: Partial<AdminUser>) {
    setUsers((rows) => rows.map((user) => (user.id === userId ? { ...user, ...patch } : user)));
  }

  function updateMembershipRow(membershipId: number, patch: Partial<AdminMembership>) {
    setMemberships((rows) =>
      rows.map((membership) => (membership.id === membershipId ? { ...membership, ...patch } : membership)),
    );
  }

  return (
    <main className="min-h-screen">
      <section className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 px-6 py-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-accent">LegalSight Administration</p>
              <h1 className="mt-2 text-3xl font-semibold text-ink">Users, roles, and matter access</h1>
              <p className="mt-2 text-sm text-slate-600">
                Manage local API-key users and matter assignments for review teams.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link href="/" className="nav-button">
                <Users size={18} />
                Workspace
              </Link>
              <Link href="/audit" className="nav-button">
                <ShieldCheck size={18} />
                Audit
              </Link>
              <button className="nav-button" onClick={() => void runAction(refresh)} type="button">
                <RefreshCw size={18} />
                Refresh
              </button>
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-4">
            <Metric label="Users" value={users.length} />
            <Metric label="Active" value={activeUsers} />
            <Metric label="Admins" value={adminUsers} />
            <Metric label="Assignments" value={memberships.length} />
          </div>

          {visibleApiKey && (
            <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900">
              <span className="font-semibold">API key:</span> <code>{visibleApiKey}</code>
            </div>
          )}
          {status && <p className="rounded-md border border-line bg-panel px-3 py-2 text-sm text-slate-700">{status}</p>}
          {error && <p className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-5 px-6 py-6 lg:grid-cols-[360px_1fr]">
        <aside className="space-y-4">
          <Panel title="Create Role">
            <label className="block">
              <span className="form-label">Role name</span>
              <input className="form-field" value={roleName} onChange={(event) => setRoleName(event.target.value)} />
            </label>
            <label className="block">
              <span className="form-label">Description</span>
              <input
                className="form-field"
                value={roleDescription}
                onChange={(event) => setRoleDescription(event.target.value)}
              />
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input checked={roleIsAdmin} onChange={(event) => setRoleIsAdmin(event.target.checked)} type="checkbox" />
              Admin role
            </label>
            <button className="primary-button" disabled={isBusy} onClick={() => void submitRole()} type="button">
              <Plus size={17} />
              Create Role
            </button>
          </Panel>

          <Panel title="Create User">
            <label className="block">
              <span className="form-label">Email</span>
              <input className="form-field" value={userEmail} onChange={(event) => setUserEmail(event.target.value)} />
            </label>
            <label className="block">
              <span className="form-label">Display name</span>
              <input className="form-field" value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
            </label>
            <label className="block">
              <span className="form-label">Organization</span>
              <input
                className="form-field"
                value={organization}
                onChange={(event) => setOrganization(event.target.value)}
              />
            </label>
            <label className="block">
              <span className="form-label">Tenant ID</span>
              <input className="form-field" value={tenantId} onChange={(event) => setTenantId(event.target.value)} />
            </label>
            <label className="block">
              <span className="form-label">Role</span>
              <select
                className="form-field"
                value={newUserRoleId ?? ""}
                onChange={(event) => setNewUserRoleId(event.target.value ? Number(event.target.value) : undefined)}
              >
                <option value="">No role</option>
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.name}
                  </option>
                ))}
              </select>
            </label>
            <button className="primary-button" disabled={isBusy} onClick={() => void submitUser()} type="button">
              <UserPlus size={17} />
              Create User
            </button>
          </Panel>

          <Panel title="Assign Matter">
            <label className="block">
              <span className="form-label">User</span>
              <select
                className="form-field"
                value={membershipUserId ?? ""}
                onChange={(event) => setMembershipUserId(event.target.value ? Number(event.target.value) : undefined)}
              >
                <option value="">Choose user</option>
                {users.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.email}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="form-label">Matter</span>
              <select
                className="form-field"
                value={membershipMatterId ?? ""}
                onChange={(event) => setMembershipMatterId(event.target.value ? Number(event.target.value) : undefined)}
              >
                <option value="">Choose matter</option>
                {matters.map((matter) => (
                  <option key={matter.id} value={matter.id}>
                    {matter.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="form-label">Assignment role</span>
              <input
                className="form-field"
                value={membershipRole}
                onChange={(event) => setMembershipRole(event.target.value)}
              />
            </label>
            <button className="secondary-button" disabled={isBusy} onClick={() => void submitMembership()} type="button">
              <Plus size={17} />
              Assign Matter
            </button>
          </Panel>
        </aside>

        <div className="space-y-5">
          <Panel title="Users">
            <div className="overflow-x-auto">
              <table className="min-w-full border-separate border-spacing-0 text-left text-sm">
                <thead className="text-slate-500">
                  <tr>
                    <th className="border-b border-line px-3 py-2">User</th>
                    <th className="border-b border-line px-3 py-2">Tenant</th>
                    <th className="border-b border-line px-3 py-2">Role</th>
                    <th className="border-b border-line px-3 py-2">Active</th>
                    <th className="border-b border-line px-3 py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td className="border-b border-line px-3 py-2 align-top">
                        <input
                          className="form-field mt-0"
                          value={user.display_name}
                          onChange={(event) => updateUserRow(user.id, { display_name: event.target.value })}
                        />
                        <p className="mt-1 text-xs text-slate-500">{user.email}</p>
                      </td>
                      <td className="border-b border-line px-3 py-2 align-top">
                        <input
                          className="form-field mt-0"
                          value={user.organization ?? ""}
                          onChange={(event) => updateUserRow(user.id, { organization: event.target.value || null })}
                          placeholder="Organization"
                        />
                        <input
                          className="form-field"
                          value={user.tenant_id ?? ""}
                          onChange={(event) => updateUserRow(user.id, { tenant_id: event.target.value || null })}
                          placeholder="Tenant ID"
                        />
                      </td>
                      <td className="border-b border-line px-3 py-2 align-top">
                        <select
                          className="form-field mt-0"
                          value={user.role_id ?? ""}
                          onChange={(event) =>
                            updateUserRow(user.id, {
                              role_id: event.target.value ? Number(event.target.value) : null,
                            })
                          }
                        >
                          <option value="">No role</option>
                          {roles.map((role) => (
                            <option key={role.id} value={role.id}>
                              {role.name}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="border-b border-line px-3 py-2 align-top">
                        <label className="inline-flex items-center gap-2">
                          <input
                            checked={user.is_active}
                            onChange={(event) => updateUserRow(user.id, { is_active: event.target.checked })}
                            type="checkbox"
                          />
                          {user.is_active ? "Active" : "Inactive"}
                        </label>
                      </td>
                      <td className="border-b border-line px-3 py-2 align-top">
                        <div className="flex flex-wrap gap-2">
                          <button
                            className="secondary-button md:w-auto"
                            disabled={isBusy}
                            onClick={() => void saveUser(user)}
                            type="button"
                          >
                            <Save size={16} />
                            Save
                          </button>
                          <button
                            className="nav-button"
                            disabled={isBusy}
                            onClick={() => void rotateKey(user)}
                            type="button"
                          >
                            <KeyRound size={16} />
                            Rotate
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>

          <Panel title="Matter Assignments">
            <div className="overflow-x-auto">
              <table className="min-w-full border-separate border-spacing-0 text-left text-sm">
                <thead className="text-slate-500">
                  <tr>
                    <th className="border-b border-line px-3 py-2">User</th>
                    <th className="border-b border-line px-3 py-2">Matter</th>
                    <th className="border-b border-line px-3 py-2">Role</th>
                    <th className="border-b border-line px-3 py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {memberships.length === 0 ? (
                    <tr>
                      <td className="px-3 py-4 text-slate-600" colSpan={4}>
                        No matter assignments yet.
                      </td>
                    </tr>
                  ) : (
                    memberships.map((membership) => (
                      <tr key={membership.id}>
                        <td className="border-b border-line px-3 py-2">{membership.user_email}</td>
                        <td className="border-b border-line px-3 py-2">{membership.matter_name}</td>
                        <td className="border-b border-line px-3 py-2">
                          <input
                            className="form-field mt-0"
                            value={membership.role}
                            onChange={(event) => updateMembershipRow(membership.id, { role: event.target.value })}
                          />
                        </td>
                        <td className="border-b border-line px-3 py-2">
                          <div className="flex flex-wrap gap-2">
                            <button
                              className="secondary-button md:w-auto"
                              disabled={isBusy}
                              onClick={() => void saveMembership(membership)}
                              type="button"
                            >
                              <Save size={16} />
                              Save
                            </button>
                            <button
                              className="nav-button"
                              disabled={isBusy}
                              onClick={() => void removeMembership(membership)}
                              type="button"
                            >
                              <Trash2 size={16} />
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Panel>
        </div>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-line bg-panel p-4">
      <p className="text-sm text-slate-600">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-md border border-line bg-white p-4">
      <h2 className="text-base font-semibold text-ink">{title}</h2>
      <div className="mt-4 space-y-3">{children}</div>
    </section>
  );
}
