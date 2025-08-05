import { useEffect } from 'react';
import { useIsMobile } from './MobileComponents';

// Hook to automatically convert desktop tables to mobile-friendly format
export const useMobileTableConverter = () => {
  const isMobile = useIsMobile();

  useEffect(() => {
    if (!isMobile) return;

    // Find all tables and wrap them with mobile-friendly version
    const tables = document.querySelectorAll('table:not(.mobile-converted)');
    
    tables.forEach((table) => {
      // Mark as converted to avoid double processing
      table.classList.add('mobile-converted');
      
      // Hide the original table
      table.style.display = 'none';
      
      // Extract table data
      const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
      const rows = Array.from(table.querySelectorAll('tbody tr'));
      
      if (headers.length === 0 || rows.length === 0) return;
      
      // Create mobile version
      const mobileContainer = document.createElement('div');
      mobileContainer.className = 'mobile-table-replacement space-y-3';
      
      rows.forEach((row) => {
        const cells = Array.from(row.querySelectorAll('td'));
        if (cells.length === 0) return;
        
        // Create mobile card for each row
        const card = document.createElement('div');
        card.className = 'mobile-card';
        
        const cardContent = document.createElement('div');
        cardContent.className = 'space-y-2';
        
        headers.forEach((header, index) => {
          if (index >= cells.length) return;
          
          const cell = cells[index];
          const cellContent = cell.innerHTML;
          
          // Skip empty cells
          if (!cellContent.trim()) return;
          
          const fieldDiv = document.createElement('div');
          fieldDiv.className = 'flex justify-between items-start';
          fieldDiv.innerHTML = `
            <div class="flex-1">
              <span class="text-sm font-medium text-gray-600">${header}:</span>
            </div>
            <div class="flex-2 text-right ml-4">
              <span class="text-sm text-gray-900">${cellContent}</span>
            </div>
          `;
          
          cardContent.appendChild(fieldDiv);
        });
        
        card.appendChild(cardContent);
        mobileContainer.appendChild(card);
      });
      
      // Insert mobile version after the original table
      table.parentNode.insertBefore(mobileContainer, table.nextSibling);
    });
    
    return () => {
      // Cleanup - show original tables and remove mobile versions
      const mobileTables = document.querySelectorAll('.mobile-table-replacement');
      mobileTables.forEach(mt => mt.remove());
      
      const convertedTables = document.querySelectorAll('table.mobile-converted');
      convertedTables.forEach(table => {
        table.style.display = '';
        table.classList.remove('mobile-converted');
      });
    };
  }, [isMobile]);
};

// Hook to optimize forms for mobile
export const useMobileFormOptimizer = () => {
  const isMobile = useIsMobile();

  useEffect(() => {
    if (!isMobile) return;

    // Find all forms and optimize them
    const forms = document.querySelectorAll('form:not(.mobile-optimized)');
    
    forms.forEach((form) => {
      form.classList.add('mobile-optimized');
      
      // Optimize input fields
      const inputs = form.querySelectorAll('input, select, textarea');
      inputs.forEach((input) => {
        // Add mobile-friendly classes
        input.classList.add('mobile-input');
        
        // Ensure minimum touch target size
        if (!input.style.minHeight) {
          input.style.minHeight = '48px';
        }
        
        // Prevent zoom on iOS
        if (input.type === 'text' || input.type === 'email' || input.type === 'tel') {
          input.style.fontSize = '16px';
        }
      });
      
      // Optimize buttons
      const buttons = form.querySelectorAll('button, input[type="submit"]');
      buttons.forEach((button) => {
        button.classList.add('touch-button');
        if (!button.style.minHeight) {
          button.style.minHeight = '48px';
        }
      });
      
      // Stack form elements vertically on mobile
      const formGroups = form.querySelectorAll('.form-group, .input-group, .flex');
      formGroups.forEach((group) => {
        if (group.classList.contains('flex')) {
          group.style.flexDirection = 'column';
          group.style.gap = '1rem';
        }
      });
    });
    
    return () => {
      // Cleanup
      const optimizedForms = document.querySelectorAll('form.mobile-optimized');
      optimizedForms.forEach(form => {
        form.classList.remove('mobile-optimized');
        
        // Remove mobile-specific styles
        const inputs = form.querySelectorAll('.mobile-input');
        inputs.forEach(input => {
          input.classList.remove('mobile-input');
          input.style.minHeight = '';
          input.style.fontSize = '';
        });
        
        const buttons = form.querySelectorAll('.touch-button');
        buttons.forEach(button => {
          button.classList.remove('touch-button');
          button.style.minHeight = '';
        });
      });
    };
  }, [isMobile]);
};

// Hook to optimize content layout for mobile
export const useMobileContentOptimizer = () => {
  const isMobile = useIsMobile();

  useEffect(() => {
    if (!isMobile) return;

    // Add mobile-optimized class to body
    document.body.classList.add('mobile-optimized');
    
    // Optimize grid layouts
    const grids = document.querySelectorAll('.grid, .flex');
    grids.forEach((grid) => {
      if (grid.classList.contains('mobile-skip')) return;
      
      grid.classList.add('mobile-adapted');
      
      // Convert multi-column grids to single column on mobile
      if (grid.classList.contains('grid')) {
        grid.style.gridTemplateColumns = '1fr';
        grid.style.gap = '1rem';
      }
      
      // Convert flex layouts to column on mobile  
      if (grid.classList.contains('flex') && !grid.classList.contains('mobile-keep-flex')) {
        grid.style.flexDirection = 'column';
        grid.style.gap = '1rem';
      }
    });
    
    // Optimize cards and containers
    const containers = document.querySelectorAll('.bg-white, .card, .panel');
    containers.forEach((container) => {
      container.classList.add('mobile-card');
    });
    
    return () => {
      // Cleanup
      document.body.classList.remove('mobile-optimized');
      
      const adaptedGrids = document.querySelectorAll('.mobile-adapted');
      adaptedGrids.forEach(grid => {
        grid.classList.remove('mobile-adapted');
        grid.style.gridTemplateColumns = '';
        grid.style.flexDirection = '';
        grid.style.gap = '';
      });
      
      const mobileCards = document.querySelectorAll('.mobile-card');
      mobileCards.forEach(card => {
        if (!card.classList.contains('mobile-card')) {
          card.classList.remove('mobile-card');
        }
      });
    };
  }, [isMobile]);
};