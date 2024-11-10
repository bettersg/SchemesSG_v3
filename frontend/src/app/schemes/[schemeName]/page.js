export default function SchemePage({ params }) {
    const { schemeName } = params;

    return (
        <div>
            <p className="text-xl font-bold">{schemeName}</p>
        </div>
    );
}
