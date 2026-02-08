import { useLocation, Link } from "react-router-dom";
import { ChevronRight, Home } from "lucide-react";

const routeNames: Record<string, string> = {
  "": "Dashboard",
  "upload": "Upload Audit",
  "audits": "All Audits",
  "search": "Global Search",
  "settings": "Settings",
  "documents": "Document Viewer",
};

export function Breadcrumbs() {
  const location = useLocation();
  const pathParts = location.pathname.split("/").filter(Boolean);
  
  if (pathParts.length === 0) {
    return (
      <nav className="flex items-center text-sm">
        <span className="font-medium text-foreground">Dashboard</span>
      </nav>
    );
  }

  return (
    <nav className="flex items-center gap-1 text-sm" aria-label="Breadcrumb">
      <Link 
        to="/" 
        className="flex items-center text-muted-foreground hover:text-foreground transition-colors"
      >
        <Home className="h-4 w-4" />
      </Link>
      
      {pathParts.map((part, index) => {
        const path = `/${pathParts.slice(0, index + 1).join("/")}`;
        const isLast = index === pathParts.length - 1;
        const name = routeNames[part] || (part.length > 20 ? `${part.slice(0, 8)}...` : part);
        
        return (
          <div key={path} className="flex items-center gap-1">
            <ChevronRight className="h-4 w-4 text-muted-foreground/50" />
            {isLast ? (
              <span className="font-medium text-foreground">{name}</span>
            ) : (
              <Link 
                to={path}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                {name}
              </Link>
            )}
          </div>
        );
      })}
    </nav>
  );
}
