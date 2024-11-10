import { Card, CardHeader, CardBody, Image, Spacer } from "@nextui-org/react";
import { Link } from "@nextui-org/react";

export default function SchemesList() {

    // TODO: Update with array from backend API
    const schemes = [
        { id: 1, name: "Scheme 1", agency: "Agency 1", description: "Description 1", route: "scheme-1" },
        { id: 2, name: "Scheme 2", agency: "Agency 2", description: "Description 2", route: "scheme-2" },
        { id: 3, name: "Scheme 3", agency: "Agency 3", description: "Description 3", route: "scheme-3" },
        { id: 4, name: "Scheme 4", agency: "Agency 4", description: "Description 4", route: "scheme-4" },
        { id: 5, name: "Scheme 5", agency: "Agency 5", description: "Description 5", route: "scheme-5" },
        { id: 6, name: "Scheme 6", agency: "Agency 6", description: "Description 6", route: "scheme-6" },
    ];

    return (
        <>
            <p className="text-base font-semibold">Search Results</p>
            <p className="text-xs text-slate-500">Showing {schemes.length} schemes</p>

            <Spacer y={3} />

            <div className="gap-2 grid grid-cols-1 sm:grid-cols-3">
                {schemes.map((scheme) => (
                    <Link key={scheme.id} href={`/schemes/${scheme.route}`} className="w-full">
                        <Card shadow="sm" className="w-full" isHoverable>
                                <CardHeader className="flex gap-3">
                                    <Image
                                        alt={`${scheme.agency} logo`}
                                        height={40}
                                        radius="sm"
                                        src="https://avatars.githubusercontent.com/u/86160567?s=200&v=4"
                                        width={40}
                                    />
                                    <div className="flex flex-col">
                                        <p className="text-md">{scheme.name}</p>
                                        <p className="text-small text-default-500">{scheme.agency}</p>
                                    </div>
                                </CardHeader>
                                <CardBody>
                                    <p className="text-small">{scheme.description}</p>
                                </CardBody>
                        </Card>
                    </Link>
                ))}
            </div>
        </>
    )
}
