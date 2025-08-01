// Função para exportar relatórios para PDF
function exportToPDF(tableId, title) {
  // Verificar se a biblioteca jsPDF está disponível
  const jspdf = window.jspdf
  if (typeof jspdf === "undefined") {
    console.error("jsPDF não está disponível. Certifique-se de incluir a biblioteca.")
    alert("Erro ao gerar PDF. A biblioteca necessária não está disponível.")
    return
  }

  try {
    const { jsPDF } = jspdf
    const doc = new jsPDF()

    // Adicionar título
    doc.setFontSize(18)
    doc.text(title, 14, 22)

    // Adicionar data
    const today = new Date()
    const dateStr = today.toLocaleDateString("pt-BR")
    doc.setFontSize(11)
    doc.text(`Gerado em: ${dateStr}`, 14, 30)

    // Obter a tabela
    const table = document.getElementById(tableId)
    if (!table) {
      console.error(`Tabela com ID ${tableId} não encontrada.`)
      alert("Erro ao gerar PDF. Tabela não encontrada.")
      return
    }

    // Configurar as colunas e linhas para o PDF
    const columns = []
    const rows = []

    // Obter cabeçalhos da tabela
    const headerRow = table.querySelector("thead tr")
    if (headerRow) {
      headerRow.querySelectorAll("th").forEach((th) => {
        // Remover elementos small dos cabeçalhos
        const headerText = th.innerText.split("\n")[0].trim()
        columns.push({ header: headerText, dataKey: headerText })
      })
    }

    // Obter dados da tabela
    table.querySelectorAll("tbody tr").forEach((tr) => {
      const rowData = {}
      tr.querySelectorAll("td").forEach((td, index) => {
        // Usar o texto do cabeçalho como chave
        const key = columns[index].header
        rowData[key] = td.innerText.trim()
      })
      rows.push(rowData)
    })

    // Adicionar rodapé se existir
    const footerRow = table.querySelector("tfoot tr")
    if (footerRow) {
      const footerData = {}
      footerRow.querySelectorAll("th").forEach((th, index) => {
        const key = columns[index].header
        footerData[key] = th.innerText.trim()
      })

      // Adicionar a data atual ao rodapé
      const today = new Date()
      const dateStr = today.toLocaleDateString("pt-BR")
      footerData["Data"] = dateStr

      rows.push(footerData)
    }

    // Gerar a tabela no PDF
    doc.autoTable({
      columns: columns,
      body: rows,
      startY: 40,
      styles: {
        fontSize: 10,
        cellPadding: 3,
        lineColor: [200, 200, 200],
      },
      headStyles: {
        fillColor: [41, 128, 185],
        textColor: 255,
        fontStyle: "bold",
      },
      alternateRowStyles: {
        fillColor: [245, 245, 245],
      },
      margin: { top: 40 },
    })

    // Obter dados de consumo por data
    const dateTable = document.getElementById("consumption-by-date-table")
    if (dateTable) {
      // Adicionar uma nova página para os dados de consumo por data
      doc.addPage()

      // Adicionar título para a seção de consumo por data
      doc.setFontSize(16)
      doc.text("Consumo por Data", 14, 22)

      // Configurar colunas para a tabela de consumo por data
      const dateColumns = [
        { header: "Data", dataKey: "Data" },
        { header: "Download (MB)", dataKey: "Download (MB)" },
        { header: "Upload (MB)", dataKey: "Upload (MB)" },
        { header: "Total (MB)", dataKey: "Total (MB)" },
      ]

      // Obter dados da tabela de consumo por data
      const dateRows = []
      dateTable.querySelectorAll("tbody tr").forEach((tr) => {
        const rowData = {}
        tr.querySelectorAll("td").forEach((td, index) => {
          const key = dateColumns[index].header
          rowData[key] = td.innerText.trim()
        })
        dateRows.push(rowData)
      })

      // Gerar a tabela de consumo por data
      doc.autoTable({
        columns: dateColumns,
        body: dateRows,
        startY: 30,
        styles: {
          fontSize: 10,
          cellPadding: 3,
          lineColor: [200, 200, 200],
        },
        headStyles: {
          fillColor: [41, 128, 185],
          textColor: 255,
          fontStyle: "bold",
        },
        alternateRowStyles: {
          fillColor: [245, 245, 245],
        },
        margin: { top: 30 },
      })
    }

    // Adicionar rodapé ao PDF
    const pageCount = doc.internal.getNumberOfPages()
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i)
      doc.setFontSize(10)
      doc.text(
        `Página ${i} de ${pageCount} - Flcomm Manager`,
        doc.internal.pageSize.width / 2,
        doc.internal.pageSize.height - 10,
        { align: "center" },
      )
    }

    // Salvar o PDF
    const filename = `${title.replace(/\s+/g, "_").toLowerCase()}_${dateStr.replace(/\//g, "-")}.pdf`
    doc.save(filename)
  } catch (error) {
    console.error("Erro ao gerar PDF:", error)
    alert("Ocorreu um erro ao gerar o PDF. Por favor, tente novamente.")
  }
}
