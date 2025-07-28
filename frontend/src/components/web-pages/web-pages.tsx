
"use client";

import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
  getPaginationRowModel,
  getSortedRowModel,
  SortingState,
  PaginationState,
} from "@tanstack/react-table";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import StartCrawlerModal from "./start-crawler-modal";
import { Input } from "@/components/ui/input";
import React from "react";
import { getWebPages } from "@/services/api";

export interface WebPage {
  id: string;
  domain: string;
  url: string;
  title: string;
  last_crawled: string;
}

const columns: ColumnDef<WebPage>[] = [
  {
    accessorKey: "domain",
    header: "Domain",
  },
  {
    accessorKey: "url",
    header: "URL",
  },
  {
    accessorKey: "title",
    header: "Title",
  },
  {
    accessorKey: "last_crawled",
    header: "Last Crawled",
  },
];

const WebPages = () => {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 10,
  });
  const [data, setData] = React.useState<{ total: number; data: WebPage[] }>({
    total: 0,
    data: [],
  });
  const [query, setQuery] = React.useState("");

  React.useEffect(() => {
    const fetchData = async () => {
      const result = await getWebPages(
        pagination.pageSize,
        pagination.pageIndex * pagination.pageSize,
        sorting[0]?.id ?? "last_crawled",
        sorting[0]?.desc ? "desc" : "asc",
        query
      );
      setData(result);
    };
    fetchData();
  }, [pagination, sorting, query]);

  const table = useReactTable({
    data: data.data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),
    onPaginationChange: setPagination,
    state: {
      sorting,
      pagination,
    },
    manualPagination: true,
    manualSorting: true,
    pageCount: Math.ceil(data.total / pagination.pageSize),
  });

  return (
    <div>
      <div className="flex items-center justify-between py-4">
        <Input
          placeholder="Search..."
          className="max-w-sm"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <StartCrawlerModal />
      </div>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                  className="even:bg-muted"
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <div className="flex items-center justify-end space-x-2 py-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
        >
          Next
        </Button>
      </div>
    </div>
  );
};

export default WebPages;
