import { FormEvent, useState } from "react";

export default function App() {
  const [income, setIncome] = useState("");
  const [taxYear, setTaxYear] = useState("2022");
  const [result, setResult] = useState<unknown>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const response = await fetch("/api/tax", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ income: Number(income), tax_year: Number(taxYear) }),
    });
    setResult(await response.json());
  }

  return (
    <main>
      <h1>Tax Calculator</h1>
      <form onSubmit={onSubmit}>
        <label>
          Annual income
          <input type="number" value={income} onChange={(e) => setIncome(e.target.value)} />
        </label>
        <label>
          Tax year
          <input type="number" value={taxYear} onChange={(e) => setTaxYear(e.target.value)} />
        </label>
        <button type="submit">Calculate</button>
      </form>
      {result !== null && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </main>
  );
}
