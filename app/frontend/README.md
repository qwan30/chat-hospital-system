# Frontend

Next.js 16 frontend for the Hospital Knowledge Assistant.

## Stack

- Next.js 16 and React 19
- TypeScript
- Tailwind CSS v4
- shadcn/ui component conventions
- TanStack Table, React Hook Form, Zod
- Recharts and Motion

## Commands

```bash
npm run dev
npm run test:workspace
npm run build
npm run lint
npm run typecheck
```

The chat workspace keeps the backend bearer token in memory only. Enter a dev token such as `dev-doctor` in the runtime control after seeding the backend; do not ship bearer tokens through public `NEXT_PUBLIC_*` variables.
