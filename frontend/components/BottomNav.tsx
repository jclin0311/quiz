"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChartIcon, HomeIcon, UserIcon } from "./Icons";

const LINKS = [
  { href: "/", label: "Today", Icon: HomeIcon },
  { href: "/dashboard", label: "Progress", Icon: ChartIcon },
  { href: "/profile", label: "Profile", Icon: UserIcon },
];

export default function BottomNav() {
  const path = usePathname();
  return (
    <nav className="nav">
      <div className="nav-inner">
        {LINKS.map(({ href, label, Icon }) => (
          <Link key={href} href={href} className={path === href ? "active" : ""}>
            <Icon />
            {label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
