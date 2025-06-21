#!/usr/bin/env python3
"""
Digital Nomad Visa Scraper
Scrapes official government sources for digital nomad visa information
"""

import asyncio
import json
import re
from datetime import datetime
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy

class VisaScraper:
    def __init__(self):
        self.countries_data = {
            "spain": {
                "name": "Spain",
                "urls": [
                    "https://www.exteriores.gob.es/Consulados/londres/en/ServiciosConsulares/Paginas/Consular/Digital-Nomad-Visa.aspx",
                    "https://prie.comercio.gob.es/en-us/paginas/teletrabajadores-caracter-internacional.aspx"
                ],
                "coordinates": {"latitude": 40.4168, "longitude": -3.7038}
            },
            "portugal": {
                "name": "Portugal", 
                "urls": [
                    "https://vistos.mne.gov.pt/en/national-visas/general-information/type-of-visa",
                    "https://www2.gov.pt/en/migrantes-viver-e-trabalhar-em-portugal/migrantes-vistos-e-autorizacoes-para-entrar-e-viver-em-portugal"
                ],
                "coordinates": {"latitude": 38.7223, "longitude": -9.1393}
            },
            "mexico": {
                "name": "Mexico",
                "urls": [
                    "https://consulmex.sre.gob.mx/leamington/index.php/non-mexicans/visas/115-temporary-resident-visa",
                    "https://www.inm.gob.mx/sae/publico/en/solicitud.html"
                ],
                "coordinates": {"latitude": 23.6345, "longitude": -102.5528}
            },
            "croatia": {
                "name": "Croatia",
                "urls": [
                    "https://mup.gov.hr/aliens-281621/temporary-stay-of-digital-nomads-286853/286853",
                    "https://digitalnomadscroatia.mup.hr/"
                ],
                "coordinates": {"latitude": 45.1000, "longitude": 15.2000}
            },
            "italy": {
                "name": "Italy",
                "urls": [
                    "https://consnewyork.esteri.it/en/servizi-consolari-e-visti/servizi-per-il-cittadino-straniero/visti/visas-to-enter-italy/digital-nomad-remote-worker-visa/"
                ],
                "coordinates": {"latitude": 41.8719, "longitude": 12.5674}
            }
        }
        
        # LLM extraction strategy for structured data
        self.extraction_strategy = LLMExtractionStrategy(
            provider="ollama/llama2",  # You can change this to openai/gpt-4 if you have API key
            api_token="your-api-token-here",  # Add your API token if using OpenAI
            schema={
                "type": "object",
                "properties": {
                    "visa_name": {"type": "string", "description": "Official name of the digital nomad visa"},
                    "min_monthly_income": {"type": "number", "description": "Minimum monthly income requirement in EUR"},
                    "eligibility_criteria": {"type": "array", "items": {"type": "string"}, "description": "List of eligibility requirements"},
                    "application_process": {"type": "array", "items": {"type": "string"}, "description": "Step-by-step application process"},
                    "required_documents": {"type": "array", "items": {"type": "string"}, "description": "List of required documents"},
                    "visa_duration": {"type": "string", "description": "Duration of the visa (e.g., '1 year, renewable')"},
                    "processing_time": {"type": "string", "description": "Expected processing time"},
                    "application_fee": {"type": "string", "description": "Cost of the visa application"},
                    "path_to_residency": {"type": "boolean", "description": "Whether this visa leads to permanent residency"},
                    "official_links": {"type": "array", "items": {"type": "string"}, "description": "Official government links"}
                },
                "required": ["visa_name", "eligibility_criteria", "application_process"]
            },
            extraction_type="schema",
            instruction="""
            Extract digital nomad visa information from this government webpage. 
            Focus on official requirements, processes, and factual information.
            Convert any income requirements to EUR if possible.
            Be precise and only extract information that is clearly stated.
            """
        )

    async def scrape_country(self, country_key):
        """Scrape visa information for a specific country"""
        country_info = self.countries_data[country_key]
        print(f"\n🌍 Scraping {country_info['name']} visa information...")
        
        all_data = []
        
        async with AsyncWebCrawler(verbose=True) as crawler:
            for url in country_info['urls']:
                try:
                    print(f"📄 Scraping: {url}")
                    
                    # Crawl the page
                    result = await crawler.arun(
                        url=url,
                        extraction_strategy=self.extraction_strategy,
                        bypass_cache=True,
                        user_agent="Mozilla/5.0 (compatible; VisaBot/1.0; +https://digitalnomadvisa.directory)"
                    )
                    
                    if result.success and result.extracted_content:
                        try:
                            extracted_data = json.loads(result.extracted_content)
                            extracted_data['source_url'] = url
                            all_data.append(extracted_data)
                            print(f"✅ Successfully extracted data from {url}")
                        except json.JSONDecodeError:
                            print(f"❌ Failed to parse JSON from {url}")
                            # Fallback: try to extract key information manually
                            manual_data = self.manual_extraction(result.markdown, url)
                            if manual_data:
                                all_data.append(manual_data)
                    else:
                        print(f"❌ Failed to scrape {url}: {result.error_message if hasattr(result, 'error_message') else 'Unknown error'}")
                        
                except Exception as e:
                    print(f"❌ Error scraping {url}: {str(e)}")
                    continue
        
        # Combine and clean data
        if all_data:
            combined_data = self.combine_country_data(country_info, all_data)
            return combined_data
        else:
            print(f"⚠️ No data extracted for {country_info['name']}")
            return None

    def manual_extraction(self, markdown_content, source_url):
        """Fallback manual extraction when LLM extraction fails"""
        print("🔧 Attempting manual extraction...")
        
        # Basic patterns to look for
        income_pattern = r'(\d+(?:,\d+)*)\s*(?:EUR|€|euros?|dollars?|\$)'
        visa_duration_pattern = r'(\d+)\s*(?:year|month)s?'
        
        # Extract income requirement
        income_match = re.search(income_pattern, markdown_content, re.IGNORECASE)
        min_income = None
        if income_match:
            income_str = income_match.group(1).replace(',', '')
            try:
                min_income = int(income_str)
            except ValueError:
                pass
        
        # Extract visa duration
        duration_match = re.search(visa_duration_pattern, markdown_content, re.IGNORECASE)
        duration = duration_match.group(0) if duration_match else "Not specified"
        
        # Basic eligibility extraction (look for common keywords)
        eligibility = []
        if "remote work" in markdown_content.lower():
            eligibility.append("Must work remotely for employer outside the country")
        if "income" in markdown_content.lower():
            eligibility.append("Proof of sufficient income required")
        if "insurance" in markdown_content.lower():
            eligibility.append("Health insurance required")
        
        return {
            "visa_name": "Digital Nomad Visa",
            "min_monthly_income": min_income,
            "eligibility_criteria": eligibility if eligibility else ["Check official source for requirements"],
            "application_process": ["Check official source for application steps"],
            "visa_duration": duration,
            "source_url": source_url,
            "extraction_method": "manual"
        }

    def combine_country_data(self, country_info, scraped_data):
        """Combine scraped data into final country entry"""
        # Take the most complete data entry
        best_data = max(scraped_data, key=lambda x: len(str(x)))
        
        # Create Sanity-compatible entry
        sanity_entry = {
            "countryName": country_info["name"],
            "slug": {"current": country_info["name"].lower().replace(" ", "-")},
            "visaName": best_data.get("visa_name", f"{country_info['name']} Digital Nomad Visa"),
            "minMonthlyIncome": best_data.get("min_monthly_income", 0),
            "briefEligibility": self.create_brief_eligibility(best_data),
            "fullEligibility": best_data.get("eligibility_criteria", []),
            "applicationProcess": best_data.get("application_process", []),
            "officialLink": best_data.get("official_links", [best_data.get("source_url", "")])[0],
            "visaDuration": best_data.get("visa_duration", "Check official source"),
            "pathToResidency": best_data.get("path_to_residency", False),
            "latitude": country_info["coordinates"]["latitude"],
            "longitude": country_info["coordinates"]["longitude"],
            "scraped_at": datetime.now().isoformat(),
            "all_sources": [item.get("source_url") for item in scraped_data if item.get("source_url")]
        }
        
        return sanity_entry

    def create_brief_eligibility(self, data):
        """Create a brief eligibility summary for the homepage"""
        criteria = data.get("eligibility_criteria", [])
        if not criteria:
            return "Remote work visa for digital nomads"
        
        # Take first 2-3 criteria and summarize
        brief_points = criteria[:2]
        return ". ".join(brief_points) + "." if brief_points else "Remote work visa for digital nomads"

    async def scrape_all_countries(self):
        """Scrape all countries and save results"""
        print("🚀 Starting visa data scraping for all countries...")
        
        all_results = {}
        
        for country_key in self.countries_data.keys():
            try:
                result = await self.scrape_country(country_key)
                if result:
                    all_results[country_key] = result
                    print(f"✅ Completed {country_key}")
                else:
                    print(f"❌ Failed to get data for {country_key}")
                    
                # Small delay between countries to be respectful
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Error processing {country_key}: {str(e)}")
                continue
        
        # Save results
        output_file = "visa_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 Scraping completed! Results saved to {output_file}")
        print(f"📊 Successfully scraped {len(all_results)} out of {len(self.countries_data)} countries")
        
        return all_results

    def generate_sanity_import_script(self, results):
        """Generate a script to import data into Sanity"""
        import_script = """
// Sanity Import Script
// Run this in your Sanity Studio or use the Sanity CLI

const visaData = """ + json.dumps(list(results.values()), indent=2) + """;

// To import this data into Sanity:
// 1. Go to your Sanity Studio
// 2. Create new Digital Nomad Visa documents
// 3. Copy the data from each entry above
// 4. Or use the Sanity CLI: sanity dataset import visa_data.ndjson production

console.log('Visa data ready for import:', visaData);
"""
        
        with open("sanity_import.js", 'w') as f:
            f.write(import_script)
        
        print("📝 Generated sanity_import.js for easy data import")

async def main():
    """Main function to run the scraper"""
    scraper = VisaScraper()
    
    # Option to scrape single country for testing
    test_mode = input("Test with single country first? (y/n): ").lower() == 'y'
    
    if test_mode:
        country = input("Enter country (spain/portugal/mexico/croatia/italy): ").lower()
        if country in scraper.countries_data:
            result = await scraper.scrape_country(country)
            if result:
                print(f"\n📋 Results for {country}:")
                print(json.dumps(result, indent=2))
        else:
            print("Invalid country. Choose from: spain, portugal, mexico, croatia, italy")
    else:
        # Scrape all countries
        results = await scraper.scrape_all_countries()
        if results:
            scraper.generate_sanity_import_script(results)

if __name__ == "__main__":
    asyncio.run(main())
