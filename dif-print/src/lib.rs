use proc_macro::TokenStream;
use quote::{quote, format_ident};
use syn::{parse_macro_input, Data, DeriveInput, Fields, Ident, Type};

#[proc_macro_derive(PrettyPrint)]
pub fn pretty_print(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = input.ident;

    let expanded = match input.data {
        Data::Struct(data_struct) => {
            let field_formatters = match data_struct.fields {
                Fields::Named(ref fields) => {
                    let field_formatters = fields.named.iter().map(|field| {
                        let field_name = field.ident.as_ref().unwrap();
                        let field_string = field_name.to_string();

                        // Check if the field is an Option type
                        if let Type::Path(type_path) = &field.ty {
                            if type_path.path.segments.last().unwrap().ident == "Option" {
                                return quote! {
                                    if let Some(ref value) = self.#field_name {
                                        result.push_str(&format!("{}: {:?}, ", #field_string, value));
                                    }
                                };
                            }
                        }

                        // If not an Option, always include the field
                        quote! {
                            result.push_str(&format!("{}: {:?}, ", #field_string, self.#field_name));
                        }
                    });
                    quote! {
                        #(#field_formatters)*
                    }
                }
                Fields::Unnamed(_) | Fields::Unit => quote! {}, // Only named fields are supported
            };

            quote! {
                impl #name {
                    pub fn pretty_print(&self) -> String {
                        let mut result = String::from("{ ");
                        #field_formatters
                        result.push_str("}");
                        result
                    }
                }
            }
        }
        _ => quote! {
            compile_error!("PrettyPrint can only be derived for structs with named fields.");
        },
    };

    TokenStream::from(expanded)
}
